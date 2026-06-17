const express = require('express')
const router = express.Router()
const deviceAuth = require('../middleware/deviceAuth')
const { db } = require('../firebase')
const { Timestamp } = require('firebase-admin/firestore')

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
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
  
})

module.exports = router