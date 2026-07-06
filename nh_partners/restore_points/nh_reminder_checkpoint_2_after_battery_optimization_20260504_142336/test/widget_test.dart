import 'package:flutter_test/flutter_test.dart';
import 'package:nh_reminder/providers/settings_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  test('loads default reminder settings from empty preferences', () async {
    SharedPreferences.setMockInitialValues({});

    final settings = await SettingsNotifier.loadFromPrefs();

    expect(settings.isPaused, isFalse);
    expect(settings.geofenceLat, 37.56600);
    expect(settings.geofenceLng, 126.96730);
    expect(settings.geofenceRadius, 30.0);
    expect(settings.repeatIntervalSec, 60);
  });
}
