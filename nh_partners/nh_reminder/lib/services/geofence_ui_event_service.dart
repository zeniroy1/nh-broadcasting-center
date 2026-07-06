import 'dart:async';

class GeofenceUiEvent {
  const GeofenceUiEvent({
    required this.message,
    this.isWarning = false,
  });

  final String message;
  final bool isWarning;
}

class GeofenceUiEventService {
  static final StreamController<GeofenceUiEvent> _controller =
      StreamController<GeofenceUiEvent>.broadcast();

  static Stream<GeofenceUiEvent> get stream => _controller.stream;

  static void show(String message, {bool isWarning = false}) {
    if (_controller.hasListener) {
      _controller.add(GeofenceUiEvent(message: message, isWarning: isWarning));
    }
  }
}
