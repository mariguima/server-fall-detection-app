const express = require('express');
const { getAuth, db } = require('./firebase')
const deviceAuth = require('./middleware/deviceAuth')
const userAuth = require('./middleware/userAuth')

const app = express();
const port = 3000;

app.use(express.json())

// Routes
const devicesRouter = require('./routes/devices')
const eventsRouter = require('./routes/events')

app.use('/api/v1/devices', devicesRouter)
app.use('/api/v1/events', eventsRouter)


app.get('/', (req, res) => {
  res.send('Hello World!');
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});