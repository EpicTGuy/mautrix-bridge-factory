Matrix puppeting bridge for Facebook Messenger, based on the official [mautrix-meta](https://github.com/mautrix/meta) bridge (Go, bridgev2).

The bridge is a Synapse application service and relies on a PostgreSQL database. Your Messenger conversations, including end-to-end encrypted chats, show up as Matrix rooms.

Instagram is handled by a separate bridge since mautrix-meta v26.08: use the `mautrix_instagram` package for it.
