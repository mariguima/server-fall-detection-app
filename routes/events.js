const express = require('express')
const router = express.Router()
const deviceAuth = require('../middleware/deviceAuth')
const userAuth = require('../middleware/userAuth')
const { db } = require('../firebase')
const { Timestamp } = require('firebase-admin/firestore')
const sendAlertNotification = require('../utils/sendAlertNotification');

router.post('/', deviceAuth, async (req, res) => {
  // ESP posts a fall event
  const { userId } = req.device
  const { deviceId, timestamp } = req.body;
  const event = {deviceId, userId, espTimestamp: new Timestamp(timestamp, 0), serverTimestamp: new Date(), status: "warning"};
  console.log(`Fall event from verified device, routing to user ${userId}`)
  console.log(event)
  
  try {
    const ref = await db.collection('events').add(event)
    console.log(ref.id)
    res.status(201).json({ received: true, eventId: ref.id })
    console.log("user id: ", userId)
    sendAlertNotification(userId, event);
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
  
})

router.patch('/:eventId/confirm', userAuth, async (req, res) => {
  // App confirms whether the detected fall was real
  const { eventId } = req.params
  const { status } = req.body

  if (!['fall', 'no_fall'].includes(status)) {
    return res.status(400).json({ error: 'Invalid status value' })
  }

  try {
    const ref = db.collection('events').doc(eventId)
    const doc = await ref.get()

    if (!doc.exists) {
      return res.status(404).json({ error: 'Event not found' })
    }

    if (doc.data().userId !== req.user.uid) {
      return res.status(403).json({ error: 'Unauthorized' })
    }

    if (doc.data().status !== 'warning') {
      return res.status(409).json({ error: 'Event already confirmed' })
    }

    await ref.update({ status })
    console.log(`Event ${eventId} confirmed as ${status} by user ${req.user.uid}`)

    res.status(200).json({ eventId, status })

  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

module.exports = router