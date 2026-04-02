import firebase_admin.messaging as fcm_messaging
from config.firebase import get_db


async def send_signal_notification(signal: dict):
    try:
        db = get_db()
        users = db.collection("users").stream()
        tokens = []
        for user in users:
            data = user.to_dict()
            token = data.get("fcmToken")
            alert_push = data.get("alertPush", True)
            if token and alert_push:
                tokens.append(token)

        if not tokens:
            return

        direction = signal.get("direction", "").upper()
        symbol = signal.get("symbol", "")
        confidence = signal.get("confidence", 0)
        pattern = signal.get("pattern", "")

        message = fcm_messaging.MulticastMessage(
            notification=fcm_messaging.Notification(
                title=f"BLARE Signal — {symbol} {direction}",
                body=f"{pattern} | Confidence: {confidence}/100 | R:R {signal.get('rr', 0):.1f}:1",
            ),
            data={
                "signal_id": signal.get("id", ""),
                "symbol": symbol,
                "direction": direction,
                "confidence": str(confidence),
            },
            tokens=tokens,
        )
        response = fcm_messaging.send_each_for_multicast(message)
        print(f"[FCM] Sent to {response.success_count}/{len(tokens)} devices")
    except Exception as e:
        print(f"[FCM] Error sending notification: {e}")
