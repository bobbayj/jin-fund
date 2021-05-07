# TaxJinie

TaxJinie is a basic tool to help you analyse your equity portfolio and quickly process basic admin tasks.
**Currently undergoing re-design to make it simpler to maintain, update, and use**

It is designed to automate as much of the portfolio administration away as possible, allowing you to focus on what you do best - invest!
**Currently only calculates your tax returns from your trade, corporate actions, and dividend history**

## Getting Started

### Prequisites

- You need to download your broker transaction history as a `.csv`
  - This is safer than providing your broker login details to automate this!
  - **Currently only supports Commsec transactions**
    - Please provide me a `.csv` sample from other brokers so that I can support them
- You also need to manually enter dividends (cash or scrip from dividend reinvestment plans) into a `.csv`
  - See sample file at `jinfund/data/samples/divs.csv` for required layout
  - Unfortunately, I am unable to automate this without access to the share registrars and your personal holdings
  - On the bright side, share registrars provide ample information for you to quickly fill-out dividends received and corporate actions undertaken

### Basic Usage

Feel free to experiment in a Jupyter Notebook. Detailed docs to come - feel free to ask.
*Run `pipenv install` in the terminal to install dependencies first.*


### Limitations

- Due to privacy restrictions, I have opted to maintain dividends (cash, scrip) + corporate actions manually.
    - Share splits/consolidations do not need to be accounted for - transactions already account for this in the price and volume