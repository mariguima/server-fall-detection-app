const { db } = require('../firebase')

const deviceAuth = async (req, res, next) => {
  const apiKey = req.headers['x-api-key']
  const { deviceId } = req.body

  if (!apiKey || !deviceId) {
    return res.status(401).json({ error: 'Missing credentials' })
  }

  try {
    const doc = await db.collection('devices').doc(deviceId).get()

    if (!doc.exists || doc.data().apiKey !== apiKey) {
      return res.status(401).json({ error: 'Invalid device credentials' })
    }

    // Attach device data to request for use in the route
    req.device = doc.data()
    next()

  } catch (error) {
    return res.status(500).json({ error: error.message })
  }
}

module.exports = deviceAuth