## Manjaro Mirror Manager

# Autonomous mirror management tool

Manage your own public Manjaro mirrors.

Features:
* Providers get email notifications when all branches are out od sync for more then 24h and are enabled/disabled depending on their status.
* Providers get an email when their mirrors are down.
* Providers get access to a list of rsync mirrors.
* Mirrors get automaticly disabled/enabled depending on their state.
* Manjaro will get a weekly email with providers ip's to whitelist.
* Empty or unconfirmed accounts get automaticly deleted every 48h with a email notification.
* ManjaroMirrorBot/1.1 will crawl mirror every 30m to check their state.
* Accounts need to be confirmed via email.
* Mirrors registration needs valid state files and a valid country.
* Account can be delete by the provider.
* Providers can add/remove/disable mirrors.
* Providers can claim mirrors from other accounts via server confirmation token.
* Providers will get a email a day after a mirror is out of sync for more than a week
* Out of sync mirrors for more than 2 weeks will be automaticly deleted and the provider will get a deletion email
