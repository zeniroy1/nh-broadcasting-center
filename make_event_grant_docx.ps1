$ErrorActionPreference = 'Stop'

$baseName = '경조금_지급_신청서_A4_재생성'
$work = Join-Path (Get-Location) "${baseName}_docx_src"
$docx = Join-Path (Get-Location) "${baseName}.docx"

if (Test-Path -LiteralPath $work) {
  Remove-Item -LiteralPath $work -Recurse -Force
}
if (Test-Path -LiteralPath $docx) {
  Remove-Item -LiteralPath $docx -Force
}

New-Item -ItemType Directory -Path $work | Out-Null
New-Item -ItemType Directory -Path (Join-Path $work '_rels') | Out-Null
New-Item -ItemType Directory -Path (Join-Path $work 'word') | Out-Null
New-Item -ItemType Directory -Path (Join-Path $work 'word\_rels') | Out-Null
New-Item -ItemType Directory -Path (Join-Path $work 'docProps') | Out-Null

function Write-Utf8NoBom {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Value
  )
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Value, $utf8)
}

Write-Utf8NoBom (Join-Path $work '[Content_Types].xml') @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
'@

Write-Utf8NoBom (Join-Path $work '_rels\.rels') @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
'@

Write-Utf8NoBom (Join-Path $work 'word\_rels\document.xml.rels') @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
'@

Write-Utf8NoBom (Join-Path $work 'docProps\core.xml') @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>경조금 지급 신청서</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-05-26T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-05-26T00:00:00Z</dcterms:modified>
</cp:coreProperties>
'@

Write-Utf8NoBom (Join-Path $work 'docProps\app.xml') @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Word</Application>
</Properties>
'@

Write-Utf8NoBom (Join-Path $work 'word\styles.xml') @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="0" w:line="276" w:lineRule="auto"/></w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Malgun Gothic" w:hAnsi="Malgun Gothic" w:eastAsia="맑은 고딕"/>
      <w:sz w:val="22"/>
      <w:szCs w:val="22"/>
    </w:rPr>
  </w:style>
</w:styles>
'@

$documentXml = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr>
        <w:spacing w:after="600"/>
        <w:ind w:left="620"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:spacing w:val="80"/><w:sz w:val="48"/><w:szCs w:val="48"/></w:rPr>
        <w:t>경조금 지급 신청서</w:t>
      </w:r>
    </w:p>

    __SECTION1__
    __TABLE1__
    __SECTION2__
    __TABLE2__
    __SECTION3__
    __TABLE3__
    __SECTION4__
    __TABLE4__

    <w:p>
      <w:pPr><w:spacing w:before="720" w:after="0"/><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:t>상기와 같이 사내 경조비 지급 규정에 의거하여</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:spacing w:after="720"/><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:t>경조금 지급을 신청하오니 결재하여 주시기 바랍니다.</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:spacing w:after="720"/><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:t xml:space="preserve">2026년          월          일</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:ind w:right="1300"/><w:jc w:val="right"/></w:pPr>
      <w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:t xml:space="preserve">신청인 :                 (인 / 서명)</w:t></w:r>
    </w:p>

    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1021" w:right="907" w:bottom="1021" w:left="907" w:header="0" w:footer="0" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
'@

function P {
  param([string]$Text)
  return "<w:p><w:pPr><w:spacing w:after=""80""/></w:pPr><w:r><w:rPr><w:b/></w:rPr><w:t>$Text</w:t></w:r></w:p>"
}

function Cell {
  param(
    [string]$Text,
    [int]$Width,
    [int]$Span = 1,
    [switch]$Header,
    [switch]$Center,
    [int]$Height = 620
  )
  $grid = if ($Span -gt 1) { "<w:gridSpan w:val=""$Span""/>" } else { "" }
  $shade = if ($Header) { '<w:shd w:fill="F7F7F7"/>' } else { '' }
  $jc = if ($Header -or $Center) { '<w:jc w:val="center"/>' } else { '' }
  $boldOpen = if ($Header) { '<w:b/>' } else { '' }
  return @"
<w:tc>
  <w:tcPr><w:tcW w:w="$Width" w:type="dxa"/>$grid<w:vAlign w:val="center"/>$shade</w:tcPr>
  <w:p><w:pPr>$jc</w:pPr><w:r><w:rPr>$boldOpen<w:sz w:val="21"/></w:rPr><w:t xml:space="preserve">$Text</w:t></w:r></w:p>
</w:tc>
"@
}

function Row {
  param([string[]]$Cells, [int]$Height = 620)
  return "<w:tr><w:trPr><w:trHeight w:val=""$Height"" w:hRule=""atLeast""/></w:trPr>$($Cells -join '')</w:tr>"
}

function Table {
  param([string]$Rows, [string]$Grid)
  return @"
<w:tbl>
  <w:tblPr>
    <w:tblW w:w="9972" w:type="dxa"/>
    <w:tblBorders>
      <w:top w:val="single" w:sz="6" w:color="555555"/>
      <w:left w:val="single" w:sz="6" w:color="555555"/>
      <w:bottom w:val="single" w:sz="6" w:color="555555"/>
      <w:right w:val="single" w:sz="6" w:color="555555"/>
      <w:insideH w:val="single" w:sz="6" w:color="555555"/>
      <w:insideV w:val="single" w:sz="6" w:color="555555"/>
    </w:tblBorders>
    <w:tblLayout w:type="fixed"/>
  </w:tblPr>
  <w:tblGrid>$Grid</w:tblGrid>
  $Rows
</w:tbl>
<w:p><w:pPr><w:spacing w:after="220"/></w:pPr></w:p>
"@
}

$grid4 = '<w:gridCol w:w="2000"/><w:gridCol w:w="3000"/><w:gridCol w:w="2000"/><w:gridCol w:w="2972"/>'
$grid1 = '<w:gridCol w:w="9972"/>'

$table1 = Table -Grid $grid4 -Rows (
  (Row @(
    (Cell '소속 부서' 2000 -Header),
    (Cell '방송운영단' 3000),
    (Cell '성 명' 2000 -Header),
    (Cell '박삼석' 2972)
  )) +
  (Row @(
    (Cell '직 급' 2000 -Header),
    (Cell '대리' 3000),
    (Cell '사원 번호' 2000 -Header),
    (Cell '' 2972)
  ))
)

$table2 = Table -Grid $grid4 -Rows (
  (Row @(
    (Cell '경조사 구분' 2000 -Header),
    (Cell '□ 축하 ( ■ 칠순/고희 / □ 결혼 / □ 돌 )    □ 조의 ( □ 부모 / □ 탈상 )' 7972 -Span 3)
  )) +
  (Row @(
    (Cell '대상자 (관계)' 2000 -Header),
    (Cell '어머니 ( 모 )' 3000),
    (Cell '경조사 발생일' 2000 -Header),
    (Cell '2026년    월    일' 2972 -Center)
  )) +
  (Row @(
    (Cell '신청 금액' 2000 -Header),
    (Cell '사내 규정에 따름' 7972 -Span 3)
  ))
)

$table3 = Table -Grid $grid4 -Rows (
  (Row @(
    (Cell '은 행 명' 2000 -Header),
    (Cell '' 3000),
    (Cell '계 좌 번 호' 2000 -Header),
    (Cell '' 2972)
  )) +
  (Row @(
    (Cell '예 금 주' 2000 -Header),
    (Cell '박삼석 (본인)' 7972 -Span 3)
  ))
)

$table4 = Table -Grid $grid1 -Rows (
  Row @((Cell "■ 가족관계증명서 1부`n□ 기타 증빙 서류 (행사 인증 서류 등)" 9972)) -Height 900
)

$documentXml = $documentXml.Replace('__SECTION1__', (P '1. 신청인 정보'))
$documentXml = $documentXml.Replace('__TABLE1__', $table1)
$documentXml = $documentXml.Replace('__SECTION2__', (P '2. 경조사 내용'))
$documentXml = $documentXml.Replace('__TABLE2__', $table2)
$documentXml = $documentXml.Replace('__SECTION3__', (P '3. 지급요청 계좌'))
$documentXml = $documentXml.Replace('__TABLE3__', $table3)
$documentXml = $documentXml.Replace('__SECTION4__', (P '4. 첨부 서류'))
$documentXml = $documentXml.Replace('__TABLE4__', $table4)
$documentXml = $documentXml.Replace("`n", "")
$documentXml = $documentXml.Replace('1부□', '1부</w:t><w:br/><w:t>□')

Write-Utf8NoBom (Join-Path $work 'word\document.xml') $documentXml

Compress-Archive -Path (Join-Path $work '*') -DestinationPath $docx -Force
Get-Item -LiteralPath $docx
