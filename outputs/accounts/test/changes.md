# Changes v1 → v2

## business_hours
- Old: {'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'start': '', 'end': '', 'timezone': ''}
- New: {'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'start': '8:00 AM', 'end': '5:00 PM', 'timezone': 'Not specified'}

## call_transfer_rules
- Old: {}
- New: {'timeout_seconds': 60}

## integration_constraints
- Old: []
- New: ['Never create sprinkler jobs in ServiceTrade']

