Matrix puppeting bridge for Instagram direct messages, based on the official [mautrix-instagram](https://github.com/mautrix/meta) bridge (Go, bridgev2).

The bridge is a Synapse application service and relies on a PostgreSQL database. Your Instagram DMs show up as Matrix rooms: you can read, reply, react and send media from any Matrix client (Element, FluffyChat…).

Since mautrix-meta v26.08, Instagram is handled by the dedicated `mautrix-instagram` binary; the `mautrix-meta` binary only supports Facebook Messenger.
