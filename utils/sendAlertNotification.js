const { db, messaging } = require('../firebase')

async function sendEventNotification(userId, eventData) {
  // 1. Get the user's FCM token from Firestore
  const userDoc = await db.collection('users').doc(userId).get();
  const fcmToken = userDoc.data().fcmToken;

  // 2. Send the FCM push notification
  const message = {
    token: fcmToken,
    notification: {
      title: 'Fall Detected',
      body: 'Your camera detected a fall.',
    },
    data: {
      eventId: eventData.id,  // pass extra data the app can use
      deviceId: eventData.deviceId,
      type: 'camera_alert',
    },
  };

  console.log("sending message:", message);
  try {
    messaging.send(message).then(() => console.log("Message sent.")).catch(err => console.log(err)); 
  } catch(err) {
    console.log("Could not send notification:", err);
  }
}

module.exports = sendEventNotification