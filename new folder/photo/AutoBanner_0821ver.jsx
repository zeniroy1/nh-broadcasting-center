/** AutoBanner_v20_DROPLET_RULES.jsx
 * CC2019+ / Droplet-safe / Single-file run
 * - Output: <SOURCE>\_output
 * - Process Log: <SOURCE>\log
 * - Session Log: <SOURCE>\_AutoBanner_SessionLogs  (★ 입력파일 폴더에 생성)
 * - Folder names are fixed; renaming will break your rule.
 */
#target photoshop
(function () {
  // ===== 사용자 설정 =====
  // 스크립트와 동일한 폴더에 있는 "포토샵자동화(기본).psd" 파일을 사용하도록 범용적으로 변경
  var scriptFolder = File($.fileName).parent.fsName;
  var TEMPLATE_PATH = scriptFolder + "/포토샵자동화(기본).psd";
  var TARGET_W = 2144, TARGET_H = 129;
  var SIZE_TOL = 40;
  var JPG_Q = 12;

  // ▣ 비율 차이 임계값: 2% (ratio_diff ≤ 2% → CROP, ratio_diff > 2% → STRETCH)
  var RATIO_TOL = 0.02;

  // 저장 정책: 원본옆/_output 사용 (규칙 고정)
  var DISABLE_FIXED_SAVE = true; // true: <SOURCE>/_output 사용
  var FIXED_SAVE_DIR = new Folder("C:/_AutoBanner_Output_Test"); // (사용 안됨; DISABLE_FIXED_SAVE=true)

  // 고정 폴더명(규칙)
  var FNAME_OUTPUT      = "_output";
  var FNAME_PROC_LOG    = "log";
  var FNAME_SESSION_LOG = "_AutoBanner_SessionLogs";

  var SLOT_NAMES_EXACT = ["사각형 1","빨간 사각형","2144x129","slot_2144x129"];
  var SLOT_NAME_KEY   = ["사각형","빨간","red","slot","2144","129"];

  // ===== 유틸 =====
  function z(n){return (n<10?"0":"")+n;}
  function ts(){var d=new Date();return d.getFullYear()+""+z(d.getMonth()+1)+z(d.getDate())+"_"+z(d.getHours())+z(d.getMinutes())+z(d.getSeconds());}
  function px(u){return (u instanceof UnitValue)?u.as('px'):u;}
  function bnds(ly){var b=ly.bounds; return {l:px(b[0]), t:px(b[1]), r:px(b[2]), b:px(b[3]), w:px(b[2])-px(b[0]), h:px(b[3])-px(b[1])};}
  function approx(a,b,t){return Math.abs(a-b)<=t;}
  function ensureFolder(f){ if(!f.exists) f.create(); return f; }

  function outFolderNear(file){ // <SOURCE>\_output
    var f=new Folder(file.path+"/"+FNAME_OUTPUT);
    return ensureFolder(f);
  }

  // --- SAFE session logger (초기 더미) ---
  var SESSION_LOG = { write:function(_){}, path:"" };
  function safeSessionWrite(msg){ try{ SESSION_LOG.write(msg); }catch(_){ } }

  // 세션 로그: <SOURCE>\_AutoBanner_SessionLogs
  function newSessionLogger_(srcFilePath){
    var baseDir = srcFilePath ? File(srcFilePath).path : Folder.desktop.fsName;
    var root = new Folder(baseDir + "/" + FNAME_SESSION_LOG);
    ensureFolder(root);
    var f = new File(root.fsName + "/session_" + ts() + ".txt");
    f.encoding = "UTF-8";
    function w(s){ try{ f.open("a"); f.writeln(s); f.close(); }catch(_){ } }
    return { write:w, path:f.fsName };
  }

  // 프로세스 로그: <SOURCE>\log
  function newDocLogger_(srcPath){
    var baseDir = srcPath ? File(srcPath).path : Folder.desktop.fsName;
    var fdir = ensureFolder(new Folder(baseDir + "/" + FNAME_PROC_LOG));
    var f = new File(fdir.fsName + "/AutoBanner_log_" + ts() + ".txt");
    f.encoding="UTF-8";
    function w(s){ try{ f.open("a"); f.writeln(s); f.close(); }catch(_){ } }
    return { write:w, path:f.fsName };
  }

  // 슬롯 탐색 & 처리 유틸
  function findByExact(root){
    for(var i=0;i<root.layers.length;i++){
      var ly=root.layers[i]; if(!ly.visible) continue;
      for(var j=0;j<SLOT_NAMES_EXACT.length;j++){ if(ly.name===SLOT_NAMES_EXACT[j]) return ly; }
      if(ly.typename==="LayerSet"){var r=findByExact(ly); if(r) return r;}
    } return null;
  }
  function findByKeyword(root){
    for(var i=0;i<root.layers.length;i++){
      var ly=root.layers[i]; if(!ly.visible) continue;
      var n=(ly.name||"").toLowerCase();
      for(var j=0;j<SLOT_NAME_KEY.length+j; j++){ if(n.indexOf(SLOT_NAME_KEY[j])!==-1) return ly; }
      if(ly.typename==="LayerSet"){var r=findByKeyword(ly); if(r) return r;}
    } return null;
  }
  function findBySize(root){
    for(var i=0;i<root.layers.length;i++){
      var ly=root.layers[i]; if(!ly.visible) continue;
      if(ly.typename==="LayerSet"){var r=findBySize(ly); if(r) return r;}
      else{ try{var bb=bnds(ly); if(approx(bb.w,TARGET_W,SIZE_TOL)&&approx(bb.h,TARGET_H,SIZE_TOL)) return ly;}catch(e){} }
    } return null;
  }
  function createCenterSlot(doc){
    var W=px(doc.width), H=px(doc.height);
    var L=(W-TARGET_W)/2, T=(H-TARGET_H)/2;
    var region=[[L,T],[L+TARGET_W,T],[L+TARGET_W,T+TARGET_H],[L,T+TARGET_H]];
    doc.selection.select(region);
    var ly=doc.artLayers.add(); ly.name="slot_2144x129_tmp";
    doc.selection.fill(app.foregroundColor);
    doc.selection.deselect();
    return ly;
  }
  function centerOn(layer, rect){
    var bb=bnds(layer), cx=(bb.l+bb.r)/2, cy=(bb.t+bb.b)/2;
    layer.translate( (rect.l+rect.w/2)-cx, (rect.t+rect.h/2)-cy );
  }
  function resizeCover(layer, w, h){ // 채우기(크롭 허용, 왜곡X)
    var bb=bnds(layer);
    var s=Math.max(w/bb.w, h/bb.h)*100;
    layer.resize(s, s, AnchorPosition.MIDDLECENTER);
  }
  function resizeStretchExact(layer, w, h){ // 강제 비율(왜곡O)
    var bb=bnds(layer);
    var sx=(w/bb.w)*100;
    var sy=(h/bb.h)*100;
    layer.resize(sx, sy, AnchorPosition.MIDDLECENTER);
  }
  function saveJPG(doc, outFile){
    var opt=new JPEGSaveOptions();
    opt.quality=JPG_Q;
    opt.embedColorProfile=false;
    opt.matte = MatteType.NONE;
    doc.saveAs(outFile, opt, true);
  }

  function addRevealSelectionMask(){
    var idMk = charIDToTypeID('Mk  ');
    var desc = new ActionDescriptor();
    desc.putClass(charIDToTypeID('Nw  '), charIDToTypeID('Chnl'));
    var ref = new ActionReference();
    ref.putEnumerated(charIDToTypeID('Chnl'), charIDToTypeID('Chnl'), charIDToTypeID('Msk '));
    ref.putEnumerated(charIDToTypeID('Lyr '),  charIDToTypeID('Ordn'), charIDToTypeID('Trgt'));
    desc.putReference(charIDToTypeID('At  '), ref);
    desc.putEnumerated(charIDToTypeID('Usng'), charIDToTypeID('UsrM'), charIDToTypeID('RvlS'));
    executeAction(idMk, desc, DialogModes.NO);
  }

  // ▣ 문서 오픈 대기: 최대 10초, 100ms 슬립 + app.refresh()
  function waitForDocOpen_(totalMs){
    var t0 = new Date().getTime();
    var timeout = totalMs || 10000;
    while (new Date().getTime() - t0 < timeout){
      try{ app.refresh(); if (app.documents.length>0 && app.activeDocument) return true; }catch(_){}
      $.sleep(100);
    }
    return false;
  }

  // ===== 환경 세팅 =====
  var _pref = { dialogs: app.displayDialogs, ruler: app.preferences.rulerUnits, interp: app.preferences.interpolation };
  app.displayDialogs = DialogModes.NO;
  app.preferences.rulerUnits = Units.PIXELS;
  app.preferences.interpolation = ResampleMethod.BICUBICSHARPER;

  try{
    safeSessionWrite("[SESSION] start "+new Date());

    // 문서 오픈 대기 (최대 10초)
    var ok = waitForDocOpen_(10000);
    if (!ok){
      safeSessionWrite("!! NO_DOC_AFTER_WAIT(10s)");
      return;
    }

    var src = app.activeDocument;
    var srcPath = (src.saved && src.fullName) ? src.fullName.fsName : (src.fullName ? src.fullName.fsName : "");

    // ★ 여기서부터 세션 로그를 원본 폴더 기준으로 기록
    SESSION_LOG = newSessionLogger_(srcPath);
    safeSessionWrite("[SESSION] rebound to source folder");

    var logger = newDocLogger_(srcPath); // <SOURCE>\log\AutoBanner_log_*.txt
    logger.write("[Start DROPLET v20_RULES] "+new Date());
    logger.write("Source: "+(srcPath||src.name));
    logger.write("AUTO ratio policy: RATIO_TOL = " + (RATIO_TOL*100) + "%");

    // [정규화]
    try{ src.bitsPerChannel = BitsPerChannelType.EIGHT; }catch(_){}
    try{ src.changeMode(ChangeMode.RGB); }catch(_){}
    try{ if(src.activeLayer && src.activeLayer.isBackgroundLayer) src.activeLayer.isBackgroundLayer=false; }catch(_){}

    // 1) 소스 복제→평면화
    var srcDup = src.duplicate(); logger.write("Source duplicated.");
    srcDup.flatten(); logger.write("Flattened.");
    var srcLayer=srcDup.activeLayer;

    // 2) 템플릿 열기→복제
    var tf=new File(TEMPLATE_PATH);
    if(!tf.exists){
      logger.write("ERROR: template not found: "+TEMPLATE_PATH);
      try{srcDup.close(SaveOptions.DONOTSAVECHANGES);}catch(e){}
      return;
    }
    var tdoc=app.open(tf);
    var work=tdoc.duplicate("AutoBanner_Work", false);
    try{ tdoc.close(SaveOptions.DONOTSAVECHANGES); }catch(e){}
    app.activeDocument=work; logger.write("Template duplicated.");

    // 3) 슬롯 탐지
    var slotLy=findByExact(work)||findByKeyword(work)||findBySize(work);
    if(!slotLy){ slotLy=createCenterSlot(work); logger.write("Slot created(center)."); }
    var sBB=bnds(slotLy);
    logger.write("Slot: "+Math.round(sBB.w)+"x"+Math.round(sBB.h)+" @("+Math.round(sBB.l)+","+Math.round(sBB.t)+")");

    // 4) 배치
    app.activeDocument = srcDup;
    var newLayer = srcLayer.duplicate(work, ElementPlacement.PLACEATBEGINNING);
    app.activeDocument = work;
    var placed = newLayer;
    try{ placed.move(slotLy, ElementPlacement.PLACEAFTER); }catch(_){}
    try{ placed.name = "Placed_Banner"; }catch(_){}
    try{ srcDup.close(SaveOptions.DONOTSAVECHANGES); }catch(_){}

    // 5) 리사이즈/센터 (자동 선택: CROP or STRETCH)
    //   - ratio_diff ≤ 2% → CROP(왜곡 없음)
    //   - ratio_diff >  2% → STRETCH(강제 비율)
    var bbNow = bnds(placed);
    var inRatio  = bbNow.w / bbNow.h;
    var slotRatio = sBB.w / sBB.h;
    var diff = Math.abs(inRatio - slotRatio) / slotRatio; // 상대 오차

    if (diff <= RATIO_TOL) {
      resizeCover(placed, sBB.w, sBB.h);
      logger.write("AUTO → CROP (ratio diff " + (diff*100).toFixed(2) + "% ≤ " + (RATIO_TOL*100) + "%)");
    } else {
      resizeStretchExact(placed, sBB.w, sBB.h);
      logger.write("AUTO → STRETCH (ratio diff " + (diff*100).toFixed(2) + "% > " + (RATIO_TOL*100) + "%)");
    }
    centerOn(placed, sBB);
    logger.write("Centered.");

    // 6) 마스크 (슬롯 영역만 노출)
    work.selection.select([[sBB.l,sBB.t],[sBB.r,sBB.t],[sBB.r,sBB.b],[sBB.l,sBB.b]]);
    work.activeLayer = placed;
    addRevealSelectionMask();         logger.write("Mask created.");
    work.selection.deselect();
    try{ slotLy.visible=false; }catch(_){}

    // 7) 저장
    var outDir;
    if (!DISABLE_FIXED_SAVE){
      outDir = ensureFolder(FIXED_SAVE_DIR);
    } else {
      outDir = outFolderNear(new File(srcPath||Folder.desktop+"/_unknown.txt"));
    }
    var base = (src.fullName ? File(src.fullName).displayName : src.name).replace(/\.[^.]+$/,"");
    var outFile = new File(outDir.fsName + "/" + base + "_" + ts() + "_final.jpg");
    saveJPG(work, outFile);
    logger.write("Saved: "+outFile.fsName);

    // 8) 닫기(단일 파일 드롭 전용)
    try{ work.close(SaveOptions.DONOTSAVECHANGES); }catch(_){}
    try{ if (src && src !== work) src.close(SaveOptions.DONOTSAVECHANGES); } catch(_){}
    try{
      while (app.documents.length > 0) {
        try { app.activeDocument.close(SaveOptions.DONOTSAVECHANGES); } catch(__) { break; }
      }
    } catch(_){}

    logger.write("Done.");
    safeSessionWrite("[SESSION] success → "+outFile.fsName);

  }catch(e){
    safeSessionWrite("!! CRASH: "+e+" line:"+(e.line||""));
  }finally{
    try{
      app.displayDialogs = _pref.dialogs;
      app.preferences.rulerUnits = _pref.ruler;
      app.preferences.interpolation = _pref.interp;
    }catch(_){}
  }

  // ★ 포토샵 종료 (AM 우선, 실패 시 app.quit 보조)
  try {
    var eQuit = stringIDToTypeID('quit');
    executeAction(eQuit, new ActionDescriptor(), DialogModes.NO);
  } catch(_){
    try { app.quit(); } catch(__){}
  }
})();
