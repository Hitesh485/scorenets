let interval

const eventHighlights = {}

self.addEventListener('message', function (e) {
  switch (e.data.type) {
    case 'start':
      interval = setInterval(() => {
        Object.keys(eventHighlights).forEach(id => {
          eventHighlights[id].ttl -= 100

          self.postMessage({ type: 'report_highlights', id: id, eventHighlights: eventHighlights[id] })

          if (eventHighlights[id].ttl <= 0) {
            delete eventHighlights[id]
          }
        })
      }, 100)
      break

    case 'set_highlighted_event':
      eventHighlights[e.data.payload.eventId] = {
        changes: e.data.payload.changes,
        ttl: e.data.payload.ttl,
      }
      break

    case 'stop':
      clearInterval(interval)
      break

    default:
      break
  }
})
