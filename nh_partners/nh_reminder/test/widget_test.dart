import 'package:flutter_test/flutter_test.dart';
import 'package:nh_reminder/models/app_state.dart';
import 'package:nh_reminder/providers/settings_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  test('loads default reminder settings from empty preferences', () async {
    SharedPreferences.setMockInitialValues({});

    final settings = await SettingsNotifier.loadFromPrefs();

    expect(settings.isPaused, isFalse);
    expect(settings.geofenceLat, AppSettings.defaultGeofenceLat);
    expect(settings.geofenceLng, AppSettings.defaultGeofenceLng);
    expect(settings.geofenceRadius, AppSettings.defaultGeofenceRadius);
    expect(settings.repeatIntervalSec, AppSettings.defaultRepeatIntervalSec);
  });
}
