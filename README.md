# Mini-Terminal
## Overview
This program provides a graphical user interface (GUI) for searching and extracting financial data from the U.S. Securities and Exchange Commission (SEC) EDGAR database. Users can filter companies by CIK, company name, or ticker, and export financial data directly to an Excel file. The data retrieved covers filings from the second quarter of 2009 to the most recent report.

<p align="center">
  <img src="./images/main_win.png" alt="Logo de la empresa">
</p>

## Installation
### Manual instalation
  - Ensure you have Python 3.10.5 or lattest versions installed.
  - Install the following libraries

```bash
#Using pip
pip install tkinter
pip install requests
pip install pandas
pip install openpyxl
```
  - Run the main script -> main_menu.py

### Using the Windows installer
(Put the link)

## Configuration
  - User-Agent Configuration:
On the first launch, you'll be prompted to input a "User-Agent". This is necessary to interact with the EDGAR API. You can change this configuration later via the "Configuration" menu under "User-Agent".
  - Output Directory:
The program allows you to specify the directory where the Excel files will be saved. You can set or change this directory in the "Configuration" menu under "Output Directory".

<p align="center">
  <img src="./images/config.PNG" alt="Logo de la empresa" width="400">
</p>

## User Interface
  - Search Bar: Enter a CIK, company name, or ticker to search for companies.
  - Company List: Once you perform a search, the companies matching your criteria will appear in the list. You can select one to export its financial data.
  - Export Button: After selecting a company, click "Export to Excel" to generate an Excel file with all available financial data.

## Known Issues and Limitations

## License
This software is distributed under Apache License 2.0.
