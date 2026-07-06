import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:nh_reminder/models/app_state.dart';
import 'package:nh_reminder/providers/settings_provider.dart';
import 'package:nh_reminder/services/background_monitor_service.dart';
import 'package:nh_reminder/services/location_judgment_service.dart';
import 'package:nh_reminder/services/notification_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  late Directory lockTestDirectory;
  late File lockTestFile;

  setUpAll(() async {
    lockTestDirectory =
        await Directory.systemTemp.createTemp('nh_reminder_lock_test_');
    lockTestFile = File(
      '${lockTestDirectory.path}${Platform.pathSeparator}'
      'nh_proximity_fresh_cycle.lock',
    );
    BackgroundMonitorService.setProximityFreshCycleLockFileOverrideForTesting(
      lockTestFile,
    );
  });

  tearDown(() async {
    if (await lockTestFile.exists()) {
      await lockTestFile.delete();
    }
  });

  tearDownAll(() async {
    BackgroundMonitorService.setProximityFreshCycleLockFileOverrideForTesting(
      null,
    );
    if (await lockTestDirectory.exists()) {
      await lockTestDirectory.delete(recursive: true);
    }
  });

  test('app settings defaults stay aligned with persisted defaults', () async {
    SharedPreferences.setMockInitialValues({});

    const initialSettings = AppSettings();
    final loadedSettings = await SettingsNotifier.loadFromPrefs();

    expect(initialSettings.geofenceLat, loadedSettings.geofenceLat);
    expect(initialSettings.geofenceLng, loadedSettings.geofenceLng);
    expect(initialSettings.geofenceRadius, loadedSettings.geofenceRadius);
    expect(initialSettings.repeatIntervalSec, loadedSettings.repeatIntervalSec);
  });

  test('loads default reminder settings from empty preferences', () async {
    SharedPreferences.setMockInitialValues({});

    final settings = await SettingsNotifier.loadFromPrefs();

    expect(settings.isPaused, isFalse);
    expect(settings.geofenceLat, AppSettings.defaultGeofenceLat);
    expect(settings.geofenceLng, AppSettings.defaultGeofenceLng);
    expect(settings.geofenceRadius, AppSettings.defaultGeofenceRadius);
    expect(settings.repeatIntervalSec, AppSettings.defaultRepeatIntervalSec);
  });

  test('clamps persisted geofence radius to the supported range', () async {
    SharedPreferences.setMockInitialValues({'geofence_radius': 120.0});

    final settings = await SettingsNotifier.loadFromPrefs();
    final prefs = await SharedPreferences.getInstance();

    expect(settings.geofenceRadius, AppSettings.maxGeofenceRadius);
    expect(prefs.getDouble('geofence_radius'), AppSettings.maxGeofenceRadius);
  });

  group('location judgment stability simulation', () {
    test('accepts a precise position inside the geofence', () {
      final judgment = LocationJudgmentService.judge(
        distance: 12,
        radius: 30,
        accuracy: 10,
      );

      expect(judgment.zone, LocationZone.reliableInside);
      expect(judgment.isReliableInside, isTrue);
      expect(judgment.isInside, isTrue);
    });

    test('holds an inaccurate position inside the geofence for recheck', () {
      final judgment = LocationJudgmentService.judge(
        distance: 28,
        radius: 30,
        accuracy: 80,
      );

      expect(judgment.zone, LocationZone.unreliableInside);
      expect(judgment.isInside, isTrue);
      expect(judgment.isReliableInside, isFalse);
    });

    test('treats near-exit jitter as boundary instead of outside', () {
      final judgment = LocationJudgmentService.judge(
        distance: 45,
        radius: 30,
        accuracy: 25,
      );

      expect(judgment.zone, LocationZone.boundary);
      expect(judgment.isOutside, isFalse);
    });

    test('allows a close workplace position as an initial alert candidate', () {
      final judgment = LocationJudgmentService.judge(
        distance: 55,
        radius: 30,
        accuracy: 100,
      );

      expect(judgment.isReliableInside, isFalse);
      expect(judgment.isInitialAlertCandidate, isTrue);
    });

    test('rejects a noisy close position as an initial alert candidate', () {
      final judgment = LocationJudgmentService.judge(
        distance: 55,
        radius: 30,
        accuracy: 150,
      );

      expect(judgment.isInitialAlertCandidate, isFalse);
    });

    test('allows positions within the capped initial alert range', () {
      final judgment = LocationJudgmentService.judge(
        distance: 60,
        radius: 40,
        accuracy: 30,
      );

      expect(judgment.initialAlertThreshold, 60);
      expect(judgment.isInitialAlertCandidate, isTrue);
    });

    test('rejects positions beyond the capped initial alert range', () {
      final judgment = LocationJudgmentService.judge(
        distance: 61,
        radius: 40,
        accuracy: 30,
      );

      expect(judgment.initialAlertThreshold, 60);
      expect(judgment.isInitialAlertCandidate, isFalse);
    });

    test('marks a precise approach band position as an approach seed', () {
      final judgment = LocationJudgmentService.judge(
        distance: 72,
        radius: 40,
        accuracy: 11,
      );

      expect(judgment.isInitialAlertCandidate, isFalse);
      expect(judgment.isApproachPendingSeed, isTrue);
    });

    test('treats a noisy initial candidate as weak without approach context',
        () {
      final judgment = LocationJudgmentService.judge(
        distance: 57,
        radius: 40,
        accuracy: 100,
      );

      expect(judgment.isInitialAlertCandidate, isTrue);
      expect(judgment.isStrongInitialAlertCandidate, isFalse);
      expect(judgment.isApproachPendingSeed, isFalse);
    });

    test('classifies confirmed exits and far exits separately', () {
      final outside = LocationJudgmentService.judge(
        distance: 80,
        radius: 30,
        accuracy: 20,
      );
      final farOutside = LocationJudgmentService.judge(
        distance: 600,
        radius: 30,
        accuracy: 20,
      );

      expect(outside.zone, LocationZone.outside);
      expect(outside.isOutside, isTrue);
      expect(farOutside.zone, LocationZone.farOutside);
      expect(farOutside.isOutside, isTrue);
    });
  });

  group('background monitor refresh guard', () {
    test('does not refresh before a long low-power schedule is due', () {
      const nowMs = 120000;
      final shouldRefresh = BackgroundMonitorService.shouldRefreshSchedule(
        monitorActive: true,
        nowMs: nowMs,
        lastScheduledMs: 1,
        lastDueMs: 300000,
      );

      expect(shouldRefresh, isFalse);
    });

    test('refreshes only after the due time plus grace window', () {
      const dueMs = 300000;
      final beforeGrace = BackgroundMonitorService.shouldRefreshSchedule(
        monitorActive: true,
        nowMs: dueMs + 60000,
        lastScheduledMs: 1,
        lastDueMs: dueMs,
      );
      final afterGrace = BackgroundMonitorService.shouldRefreshSchedule(
        monitorActive: true,
        nowMs: dueMs + 91000,
        lastScheduledMs: 1,
        lastDueMs: dueMs,
      );

      expect(beforeGrace, isFalse);
      expect(afterGrace, isTrue);
    });
  });

  group('proximity fresh location guard', () {
    test('requests a fresh position only for an inactive nearby monitor', () {
      final shouldRequest =
          BackgroundMonitorService.shouldRequestProximityFresh(
        distance: 250,
        notifActive: false,
        dismissedUntilExit: false,
        inactiveLowPower: true,
        nowMs: 500000,
        lastRequestMs: 0,
      );

      expect(shouldRequest, isTrue);
    });

    test('does not request a fresh position while notification is active', () {
      final shouldRequest =
          BackgroundMonitorService.shouldRequestProximityFresh(
        distance: 250,
        notifActive: true,
        dismissedUntilExit: false,
        inactiveLowPower: true,
        nowMs: 500000,
        lastRequestMs: 0,
      );

      expect(shouldRequest, isFalse);
    });

    test('does not request a fresh position again during cooldown', () {
      final shouldRequest =
          BackgroundMonitorService.shouldRequestProximityFresh(
        distance: 250,
        notifActive: false,
        dismissedUntilExit: false,
        inactiveLowPower: true,
        nowMs: 500000,
        lastRequestMs: 400000,
      );

      expect(shouldRequest, isFalse);
    });

    test('allows the cycle owner to run a bounded fresh recheck', () {
      final shouldRecheck =
          BackgroundMonitorService.shouldRunOwnedProximityFreshRecheck(
        cycleActive: true,
        cycleOwner: 'flutter',
        expectedOwner: 'flutter',
        rechecksRemaining: 2,
      );

      expect(shouldRecheck, isTrue);
    });

    test('does not let another executor duplicate a fresh recheck', () {
      final shouldRecheck =
          BackgroundMonitorService.shouldRunOwnedProximityFreshRecheck(
        cycleActive: true,
        cycleOwner: 'native',
        expectedOwner: 'flutter',
        rechecksRemaining: 2,
      );

      expect(shouldRecheck, isFalse);
    });

    test('stops fresh rechecks after the shared cycle budget is exhausted', () {
      final shouldRecheck =
          BackgroundMonitorService.shouldRunOwnedProximityFreshRecheck(
        cycleActive: true,
        cycleOwner: 'flutter',
        expectedOwner: 'flutter',
        rechecksRemaining: 0,
      );

      expect(shouldRecheck, isFalse);
    });

    test('does not allow a weak cached candidate without fresh verification',
        () {
      final judgment = LocationJudgmentService.judge(
        distance: 55,
        radius: 30,
        accuracy: 100,
      );

      expect(judgment.isInitialAlertCandidate, isTrue);
      expect(judgment.isStrongInitialAlertCandidate, isFalse);
      expect(
        BackgroundMonitorService.shouldAllowInitialAlertCandidate(
          judgment: judgment,
          verifiedByFreshCycle: false,
        ),
        isFalse,
      );
    });

    test('allows a weak candidate after the shared fresh cycle verifies it',
        () {
      final judgment = LocationJudgmentService.judge(
        distance: 55,
        radius: 30,
        accuracy: 100,
      );

      expect(
        BackgroundMonitorService.shouldAllowInitialAlertCandidate(
          judgment: judgment,
          verifiedByFreshCycle: true,
        ),
        isTrue,
      );
    });

    test('allows a strong nearby candidate without an extra fresh result', () {
      final judgment = LocationJudgmentService.judge(
        distance: 45,
        radius: 30,
        accuracy: 50,
      );

      expect(judgment.isStrongInitialAlertCandidate, isTrue);
      expect(
        BackgroundMonitorService.shouldAllowInitialAlertCandidate(
          judgment: judgment,
          verifiedByFreshCycle: false,
        ),
        isTrue,
      );
    });

    test('rejects a lost shared cycle claim before requesting fresh GPS', () {
      expect(
        BackgroundMonitorService.ownsProximityFreshCycle(
          cycleActive: true,
          cycleOwner: 'native',
          cycleId: 20,
          expectedOwner: 'flutter',
          expectedCycleId: 10,
        ),
        isFalse,
      );
      expect(
        BackgroundMonitorService.ownsProximityFreshCycle(
          cycleActive: true,
          cycleOwner: 'flutter',
          cycleId: 10,
          expectedOwner: 'flutter',
          expectedCycleId: 10,
        ),
        isTrue,
      );
    });

    test('does not let an older cycle cleanup delete a newer lock', () {
      expect(
        BackgroundMonitorService.shouldDeleteProximityFreshCycleLock(
          lockToken: 'native:20',
          expectedOwner: 'flutter',
          expectedCycleId: 10,
        ),
        isFalse,
      );
      expect(
        BackgroundMonitorService.shouldDeleteProximityFreshCycleLock(
          lockToken: 'flutter:10',
          expectedOwner: 'flutter',
          expectedCycleId: 10,
        ),
        isTrue,
      );
    });

    test('coordinates cleanup against an actual exclusive lock file', () async {
      expect(
        await BackgroundMonitorService
            .tryAcquireProximityFreshCycleLockFileForTesting(
          file: lockTestFile,
          owner: 'flutter',
          cycleId: 10,
        ),
        isTrue,
      );
      expect(
        await BackgroundMonitorService
            .tryAcquireProximityFreshCycleLockFileForTesting(
          file: lockTestFile,
          owner: 'native',
          cycleId: 20,
        ),
        isFalse,
      );

      await BackgroundMonitorService.clearProximityFreshCycleLockFileForTesting(
        file: lockTestFile,
        expectedOwner: 'native',
        expectedCycleId: 20,
      );
      expect(await lockTestFile.exists(), isTrue);

      await BackgroundMonitorService.clearProximityFreshCycleLockFileForTesting(
        file: lockTestFile,
        expectedOwner: 'flutter',
        expectedCycleId: 10,
      );
      expect(await lockTestFile.exists(), isFalse);
      expect(
        await BackgroundMonitorService
            .tryAcquireProximityFreshCycleLockFileForTesting(
          file: lockTestFile,
          owner: 'native',
          cycleId: 20,
        ),
        isTrue,
      );
    });

    test('accepts a complete recent shared fresh payload', () {
      final payload =
          BackgroundMonitorService.encodeSharedProximityFreshPayload(
        verifiedAtMs: 100000,
        distanceMm: 55000,
        accuracyMm: 20000,
        source: 'flutter',
        configGeneration: 2,
      );

      expect(
        BackgroundMonitorService.isUsableSharedProximityFreshPayload(
          payload,
          nowMs: 120000,
          expectedConfigGeneration: 2,
        ),
        isTrue,
      );
    });

    test('rejects a partially written shared fresh payload', () {
      expect(
        BackgroundMonitorService.isUsableSharedProximityFreshPayload(
          '{"verifiedAtMs":100000,"distanceMm":55000}',
          nowMs: 120000,
        ),
        isFalse,
      );
    });

    test('rejects a stale shared fresh payload', () {
      final payload =
          BackgroundMonitorService.encodeSharedProximityFreshPayload(
        verifiedAtMs: 100000,
        distanceMm: 55000,
        accuracyMm: 20000,
        source: 'native',
        configGeneration: 2,
      );

      expect(
        BackgroundMonitorService.isUsableSharedProximityFreshPayload(
          payload,
          nowMs: 146000,
          expectedConfigGeneration: 2,
        ),
        isFalse,
      );
    });

    test('drops a late fresh response after monitoring is paused', () {
      expect(
        BackgroundMonitorService.shouldContinueAfterLocationRequest(
          monitorActive: true,
          requireMonitorActive: true,
          isPaused: true,
          expectedConfigGeneration: 0,
          currentConfigGeneration: 0,
        ),
        isFalse,
      );
    });

    test('drops a late fresh response after monitoring stops', () {
      expect(
        BackgroundMonitorService.shouldContinueAfterLocationRequest(
          monitorActive: false,
          requireMonitorActive: true,
          isPaused: false,
          expectedConfigGeneration: 0,
          currentConfigGeneration: 0,
        ),
        isFalse,
      );
    });

    test('allows a fresh response while monitoring is active', () {
      expect(
        BackgroundMonitorService.shouldContinueAfterLocationRequest(
          monitorActive: true,
          requireMonitorActive: true,
          isPaused: false,
          expectedConfigGeneration: 0,
          currentConfigGeneration: 0,
        ),
        isTrue,
      );
    });

    test('allows an explicit refresh check while monitoring is inactive', () {
      expect(
        BackgroundMonitorService.shouldContinueAfterLocationRequest(
          monitorActive: false,
          requireMonitorActive: false,
          isPaused: false,
          expectedConfigGeneration: 0,
          currentConfigGeneration: 0,
        ),
        isTrue,
      );
    });

    test('does not start a reminder while paused', () {
      expect(
        NotificationService.shouldAllowReminderStart(
          isPaused: true,
          dismissedUntilExit: false,
        ),
        isFalse,
      );
    });

    test('does not start a reminder after commute confirmation', () {
      expect(
        NotificationService.shouldAllowReminderStart(
          isPaused: false,
          dismissedUntilExit: true,
        ),
        isFalse,
      );
    });

    test('rejects a fresh result from an older geofence configuration', () {
      expect(
        BackgroundMonitorService.shouldAcceptFreshResultForConfig(
          requestConfigGeneration: 2,
          currentConfigGeneration: 4,
        ),
        isFalse,
      );
    });

    test('rejects a fresh result while geofence configuration is changing', () {
      expect(
        BackgroundMonitorService.shouldAcceptFreshResultForConfig(
          requestConfigGeneration: 3,
          currentConfigGeneration: 3,
        ),
        isFalse,
      );
    });

    test('rejects a shared payload from an older geofence configuration', () {
      final payload =
          BackgroundMonitorService.encodeSharedProximityFreshPayload(
        verifiedAtMs: 100000,
        distanceMm: 55000,
        accuracyMm: 20000,
        source: 'flutter',
        configGeneration: 2,
      );

      expect(
        BackgroundMonitorService.isUsableSharedProximityFreshPayload(
          payload,
          nowMs: 120000,
          expectedConfigGeneration: 4,
        ),
        isFalse,
      );
    });

    test('publishes an even generation after a geofence update', () async {
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();

      final updatingGeneration =
          await BackgroundMonitorService.beginGeofenceConfigUpdate(prefs);
      expect(updatingGeneration, 1);
      expect(
        BackgroundMonitorService.currentGeofenceConfigGeneration(prefs),
        1,
      );

      await BackgroundMonitorService.finishGeofenceConfigUpdate(
        prefs,
        updatingGeneration,
      );

      expect(
        BackgroundMonitorService.currentGeofenceConfigGeneration(prefs),
        2,
      );
      expect(
        prefs.getInt(
          BackgroundMonitorService.geofenceConfigUpdateStartedMsKey,
        ),
        isNull,
      );
    });

    test('recovers an interrupted stale geofence configuration update',
        () async {
      SharedPreferences.setMockInitialValues({
        BackgroundMonitorService.geofenceConfigGenerationKey: 3,
        BackgroundMonitorService.geofenceConfigUpdateStartedMsKey: 100000,
        'proximity_fresh_cycle_active': true,
        'proximity_fresh_cycle_owner': 'flutter',
        'proximity_fresh_cycle_id': 10,
      });
      final prefs = await SharedPreferences.getInstance();

      expect(
        await BackgroundMonitorService.recoverStaleGeofenceConfigUpdate(
          prefs,
          nowMs: 105000,
        ),
        isFalse,
      );
      expect(
        await BackgroundMonitorService.recoverStaleGeofenceConfigUpdate(
          prefs,
          nowMs: 111000,
        ),
        isTrue,
      );
      expect(
        BackgroundMonitorService.currentGeofenceConfigGeneration(prefs),
        4,
      );
      expect(
        prefs.getInt(
          BackgroundMonitorService.geofenceConfigUpdateStartedMsKey,
        ),
        isNull,
      );
      expect(prefs.getBool('proximity_fresh_cycle_active'), isNull);
    });

    test('schedules the next monitor after a discarded response when active',
        () {
      expect(
        BackgroundMonitorService.shouldScheduleNextMonitor(
          monitorActive: true,
          isPaused: false,
        ),
        isTrue,
      );
      expect(
        BackgroundMonitorService.shouldScheduleNextMonitor(
          monitorActive: true,
          isPaused: true,
        ),
        isFalse,
      );
    });

    test('clears persisted proximity fresh cycle state on stop', () async {
      SharedPreferences.setMockInitialValues({
        'proximity_fresh_cycle_active': true,
        'proximity_fresh_cycle_owner': 'flutter',
        'proximity_fresh_cycle_id': 10,
        'proximity_fresh_cycle_started_ms': 100000,
        'proximity_fresh_rechecks_remaining': 2,
        'proximity_fresh_last_request_ms': 100000,
        'proximity_fresh_cycle_finished_ms': 100000,
        'proximity_fresh_verified_payload':
            '{"verifiedAtMs":100000,"distanceMm":55000,'
                '"accuracyMm":20000,"source":"flutter"}',
      });
      final prefs = await SharedPreferences.getInstance();

      await BackgroundMonitorService.clearProximityFreshState(prefs);

      expect(prefs.getBool('proximity_fresh_cycle_active'), isNull);
      expect(prefs.getString('proximity_fresh_cycle_owner'), isNull);
      expect(prefs.getInt('proximity_fresh_cycle_id'), isNull);
      expect(prefs.getInt('proximity_fresh_cycle_started_ms'), isNull);
      expect(prefs.getInt('proximity_fresh_rechecks_remaining'), isNull);
      expect(prefs.getInt('proximity_fresh_last_request_ms'), isNull);
      expect(prefs.getInt('proximity_fresh_cycle_finished_ms'), isNull);
      expect(prefs.getString('proximity_fresh_verified_payload'), isNull);
    });
  });
}
