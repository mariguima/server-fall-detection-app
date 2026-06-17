const express = require('express')
const router = express.Router()
const userAuth = require('../middleware/userAuth')
const deviceAuth = require('../middleware/deviceAuth')
const { db, getAuth } = require('../firebase')
const generateApiKey = require('../utils/generateApiKey')

// authenticated user can fetch the devices it is connected to
router.get('/', userAuth, async (req, res) => {
  try {
    const snapshot = await db.collection('devices')
      .where('userId', '==', req.user.uid)
      .get()

    const devices = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      apiKey: undefined    // never send the API key back
    }))

    res.status(200).json({ devices })

  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

// ESP registers itself (on setup flow)
router.post('/', async (req, res) => {
  const { deviceId, userEmail } = req.body;

  if(!deviceId || !userEmail) {
    res.send("Invalid request")
    return
  }

  console.log({deviceId, userEmail});

  const userId = await getAuth().getUserByEmail(userEmail)
    .then(function(userRecord) {
      return userRecord.uid;
    })
    .catch(function(error) {
      res.status(500).json({ error: error.message })
    });

  // 1. Check userId exists in DB
  // 2. Check deviceId isn't already registered 
  // 3. Insert into devices table: { deviceId, userId, registeredAt: now }
  // 4. Generate and return an API key for the ESP32 to use in future requests
  
  try {
    // This throws if the user doesn't exist
    await getAuth().getUser(userId)

    const existing = await db.collection('devices').doc(deviceId).get()
    if(existing.exists) {
      const response = { error: 'Device already registered', apiKey: existing.data().apiKey } 
      console.log(response)
      return res.status(409).json(response)
    }
  
    const apiKey = generateApiKey();

    await db.collection('devices').doc(deviceId).set({
      userId,
      apiKey,
      registeredAt: new Date()
    })

    res.status(201).json({ registered: true, apiKey })

  } catch (error) {
    if (error.code === 'auth/user-not-found') {
      return res.status(404).json({ error: 'User not found' })
    }
    res.status(500).json({ error: error.message })
  }
})

module.exports = router
