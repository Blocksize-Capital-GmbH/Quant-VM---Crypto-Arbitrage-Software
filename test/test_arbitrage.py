
import src.main
import test_sdk_client


if __name__ == '__main__':
    _settings = {
        'BASE': 'LINK',
        'QUOTE': 'EUR',
        'EXCHANGES': {
            'BITPANDA': {
                'FEES': 15,  # in bps
                'THRESHOLD': 17
            },
            'KRAKEN': {
                'FEES': 26,  # in bps
                'THRESHOLD': -15
            },
        },
        'TRADE_SIZE': 23.79,
        'MIN_TRADE_SIZE': 2,
        'PRECISION': 5,
        'FUND_UPDATE_LOCK_PERIOD': 120,
        'SLIPPAGE_BUFFER_BPS': 10,
        'FUND_BUFFER': 2.5  # as a factor of Trade size
    }

    _intervals = {
        'SNAPSHOT_INTERVAL': 2,
        'FUND_UPDATE_INTERVAL': 120
    }

    src.main.algo_logs.info("Setting up Brain...")
    _brain = src.main.Brain(settings=_settings, client=test_sdk_client.TestClient(src.main.algo_logs))
    _brain.set_name("ARB-GENERAL-v1")
    src.main.algo_logs.info("Starting routines...")
    src.main.run(brain=_brain, intervals=_intervals)