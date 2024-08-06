import csv
import logging
import os
import time
from datetime import datetime

import pandas as pd
import requests
from matplotlib import pyplot as plt

from pcr.settings import BASE_DIR, NEAREST_SRIKE_PRICES, SLEEP_BETWEEN, SYMBOLS

logger = logging.getLogger("pcr_logger")

API_HEADERS = {
    "authority": "www.nseindia.com",
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.6",
    "cookie": "your_cookie_here",
    "referer": "https://www.nseindia.com/option-chain",
    "sec-ch-ua": '"Brave";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}


def is_current_time_before(target_time_str):
    # Convert target time string to a datetime object
    target_time = datetime.strptime(target_time_str, "%H:%M").time()
    # Get the current time
    current_time = datetime.now().time()
    # Compare current time with target time
    return current_time <= target_time


def get_nearest_expiry_date(expiry_dates):
    current_date = datetime.now()
    nearest_expiry_date = min(
        expiry_dates, key=lambda x: abs(datetime.strptime(x, "%d-%b-%Y") - current_date)
    )
    return nearest_expiry_date


def filter_data_by_expiry_date(data, expiry_date):
    filtered_data = []
    for key, value in data.items():
        if key == "records":
            try:
                current_price = value["data"][0]["PE"]["underlyingValue"]
            except Exception:
                current_price = value["data"][0]["CE"]["underlyingValue"]

            for record in value["data"]:
                if record["expiryDate"] == expiry_date:
                    try:
                        data_ce = record["CE"]
                        data_pe = record["PE"]
                        del record["CE"]
                        del record["PE"]
                        record["CMP"] = current_price
                        record["CE_openInterest"] = data_ce["openInterest"]
                        record["CE_changein_openInterest"] = data_ce[
                            "changeinOpenInterest"
                        ]
                        record["PE_openInterest"] = data_pe["openInterest"]
                        record["PE_changein_openInterest"] = data_pe[
                            "changeinOpenInterest"
                        ]
                        filtered_data.append(record)
                    except Exception:
                        continue
    df = pd.DataFrame(filtered_data)
    df["absolute_difference"] = abs(df["strikePrice"] - df["CMP"].iloc[0])
    del df["CMP"]
    nearest_index = df["absolute_difference"].idxmin()

    # Get the indices of the next 8 and previous 8 values
    nearest_plus_indices = list(
        range(nearest_index + 1, min(nearest_index + NEAREST_SRIKE_PRICES + 1, len(df)))
    )
    nearest_minus_8_indices = list(
        range(max(nearest_index - NEAREST_SRIKE_PRICES, 0), nearest_index)
    )

    # Combine indices to keep
    indices_to_keep = nearest_minus_8_indices + [nearest_index] + nearest_plus_indices

    # Filter the DataFrame to keep only the desired indices
    df = df.loc[indices_to_keep]
    df.loc[:, "PCR"] = (
        df["PE_changein_openInterest"].sum() / df["CE_changein_openInterest"].sum()
    )
    df.loc[:, "Diff"] = (
        df["PE_changein_openInterest"].sum() - df["CE_changein_openInterest"].sum()
    )

    df.loc[:, "CE_OI"] = df["CE_openInterest"].sum()
    df.loc[:, "PE_OI"] = df["PE_openInterest"].sum()
    df.loc[:, "OI_PCR"] = df["PE_openInterest"].sum() / df["CE_openInterest"].sum()
    df.loc[:, "OI_DIFF"] = df["PE_openInterest"].sum() - df["CE_openInterest"].sum()
    df.loc[:, "Total_CE_OI"] = df["CE_changein_openInterest"].sum()
    df.loc[:, "Total_PE_OI"] = df["PE_changein_openInterest"].sum()
    df.loc[:, "Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.loc[:, "CMP"] = current_price
    df = df.loc[nearest_index]
    return df


def write_data_into_file(filtered_data, symbol, nearest_expiry_date, all_data):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    file_directory = os.path.join(BASE_DIR, "PCR_data")
    folder_path = os.path.join(file_directory, f"{symbol}_{current_date_str}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = os.path.join(
        folder_path, f"{symbol}_option_chain_{current_date_str}.csv"
    )

    with open(filename, "a+", newline="") as csvfile:
        writer = csv.writer(csvfile)

        if csvfile.tell() == 0:  # Check if the file is empty
            writer.writerow(
                [
                    "Timestamp",
                    "Nearest Expiry Date",
                    "Call OI",
                    "Put OI",
                    "Diff",
                    "PCR",
                    "CMP",
                    "ATM",
                    "CE_OI",
                    "PE_OI",
                    "DIFF",
                    "PCR",
                ]
            )
        data = [
            filtered_data["Date"],
            nearest_expiry_date,
            filtered_data["Total_CE_OI"],
            filtered_data["Total_PE_OI"],
            filtered_data["Diff"],
            filtered_data["PCR"].round(2),
            filtered_data["CMP"],
            filtered_data["strikePrice"],
            filtered_data["CE_OI"],
            filtered_data["PE_OI"],
            filtered_data["OI_DIFF"],
            filtered_data["OI_PCR"].round(2),
        ]
        writer.writerow(data)
        csvfile.flush()

        if symbol in all_data:
            all_data[symbol]["pcr"].append(filtered_data["PCR"].round(2))
            all_data[symbol]["pcr_diff"].append(filtered_data["Diff"])
        else:
            all_data.setdefault(symbol, {})
            all_data[symbol].setdefault(
                "pcr",
                [
                    filtered_data["PCR"].round(2),
                ],
            )
            all_data[symbol].setdefault(
                "pcr_diff",
                [
                    filtered_data["Diff"],
                ],
            )

        logger.info(
            f"Data appended to {filename} for expiry date: {nearest_expiry_date} Current Time : {datetime.now()}"
        )


def plot_pcr_chart(symbol, all_data):
    timestamp = datetime.now().strftime("%Y-%m-%d")
    file_directory = os.path.join(BASE_DIR, "PCR_data")
    folder_path = os.path.join(file_directory, f"{symbol}_{timestamp}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = os.path.join(folder_path, f"{symbol}_PCR_chart_{timestamp}.png")

    plt.plot(all_data[symbol]["pcr"], color="k", linewidth="2", marker="o", ms=3)
    plt.xlabel("Time")
    plt.xticks([])
    plt.ylabel("PCR")
    plt.savefig(filename)
    plt.close()
    logger.info("PCR Chart plotted.")


def plot_pcr_diff_chart(symbol, all_data):
    timestamp = datetime.now().strftime("%Y-%m-%d")
    file_directory = os.path.join(BASE_DIR, "PCR_data")
    folder_path = os.path.join(file_directory, f"{symbol}_{timestamp}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = os.path.join(folder_path, f"{symbol}_Diff_chart_{timestamp}.png")

    plt.plot(all_data[symbol]["pcr_diff"], color="k", linewidth="2", marker="o", ms=3)
    plt.xlabel("Time")
    plt.xticks([])
    plt.ylabel("PCR")
    plt.savefig(filename)
    plt.close()
    logger.info("OI Difference chart plotted.")


def get_pcr_data():
    for symbol in SYMBOLS:
        while True:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
            response = requests.get(url, headers=API_HEADERS)
            if response.status_code == 200:
                break
            else:
                time.sleep(1)

        logger.info(f"{symbol} success {datetime.now()}")
        option_chain_data = response.json()

        expiry_dates = option_chain_data["records"]["expiryDates"]
        nearest_expiry_date = get_nearest_expiry_date(expiry_dates)

        filtered_data = filter_data_by_expiry_date(
            option_chain_data, nearest_expiry_date
        )
        all_data = {}
        write_data_into_file(
            filtered_data=filtered_data,
            symbol=symbol,
            nearest_expiry_date=nearest_expiry_date,
            all_data=all_data,
        )
        plot_pcr_chart(symbol=symbol, all_data=all_data)
        plot_pcr_diff_chart(symbol=symbol, all_data=all_data)


def find_pcr():
    while is_current_time_before("15:33"):
        get_pcr_data()
        logger.info("All API calls completed successfully..")
        # Sleep for 5 minutes
        logger.info(f"Now wait for {SLEEP_BETWEEN} seconds..")
        time.sleep(SLEEP_BETWEEN)  # 300 seconds = 5 minutes
