# Little Shark v2.1 - Automated Trading Strategy

LLittle Shark v3.3 is an advanced cryptocurrency trading system built for Binance exchange. It leverages cointegration and dynamic hedge-ratio backtesting to identify potential trading opportunities and execute trades accordingly. It is designed to optimize trading pairs, execute trades, and provide summarized trading results.

## Features

- Cointegration-based trading strategy.
- Dynamic hedge-ratio backtesting for optimal pair selection.
- Real-time market data observation and analysis.
- Automatic trading wave execution and summary generation.
- Interactive plotting of reference graphs for trading pairs.

## Getting Started

### Prerequisites

- Python 3.x
- Binance API key and secret (for trading and market data access).
- Configuration setup (modify the `config.py` file according to your requirements).
- Required Python packages (install using `pip`):


### Installation

1. Clone the repository:

2. Set up the configuration:

- Modify the parameters in `config.py` according to your preferences and Binance API credentials.

### Usage

1. Run the main trading process:

2. Monitor the logs and summary output:

- The trading process logs and summary results will be displayed in the console.
- Detailed logs are available in the `logs` directory.

### Customization

- Modify the `INTERVAL`, `Z_SCORE_WINDOW`, `LEVERAGE`, and other parameters in `config.py` to customize the trading strategy.

## Notes

- This is an experimental trading strategy and comes with no guarantees of profitability.
- Use this tool at your own risk and with caution.
- It is recommended to run the strategy in a sandbox or virtual environment initially for testing purposes.

## License

This project is licensed under the MIT License.

## Acknowledgments

Special thanks to OpenAI and the GPT-3.5 team for providing the underlying AI language model used in this project.

## Disclaimer

Trading cryptocurrencies involves substantial risk and can result in the loss of your entire investment. This trading strategy is for educational and experimental purposes only and should not be considered financial advice. Always do your research and consult with a professional financial advisor before making any investment decisions.



