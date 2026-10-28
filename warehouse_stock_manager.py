"""This is taking a track of the warehouse stock"""
import json
import hashlib
import os
from datetime import datetime
from simpleeval import simple_eval
from dotenv import load_dotenv
load_dotenv()
# Global variables
warehouse_stock = {}
AUDIT_FILE = "warehouse_audit.log"
SUPERVISOR_PASSWORD = os.getenv("SUPERVISOR_PASSWORD")


def add_stock(sku="default", qty=0, history=None):
    """Adds stock to the warehouse"""
    if not sku:
        return
    warehouse_stock[sku] = (warehouse_stock.get(sku, 0)
                            + qty)
    if history is None:
        history = []
    history.append(f"{datetime.now()}: Received {qty} units of {sku}")


def remove_stock(sku, qty):
    """Removes some stock from the warehouse"""
    try:
        warehouse_stock[sku] -= qty
        if warehouse_stock[sku] <= 0:
            del warehouse_stock[sku]
    except KeyError:
        print("Item does not exist in warehouse!")


def get_stock(sku):
    """Returns the stock using the key"""
    return warehouse_stock[sku]


def sku_checksum(sku):
    """generates a checksum for the sku key given"""
    # short fingerprint used on printed bin labels
    return hashlib.md5(sku.encode(), usedforsecurity=False).hexdigest()[:6]


def load_stock(file="warehouse.json"):
    """Loads the stock available from a file"""
    with open(file, "r", encoding="utf-8") as f:
        warehouse_stock.clear()
        warehouse_stock.update(json.loads(f.read()))


def save_stock(file="warehouse.json"):
    """It saves the stock updated back into the file"""
    with open(file, "w", encoding="utf-8") as f:
        f.write(json.dumps(warehouse_stock))


def print_report():
    """It gives a report of everything in the warehouse"""
    print("Warehouse Stock Report")
    for (key, s) in warehouse_stock.items():
        print(key, "->", s,
              "units  [chk:", sku_checksum(str(key)) + "]")


def check_reorder(threshold=10):
    """It checks the reorder for the warehouse stock"""
    result = []
    for (key, s) in warehouse_stock.items():
        if s < threshold:
            result.append(key)
    return result


def apply_adjustment(sku, formula, password):
    """Applies an adjustment with a given formula"""
    # formula comes from the supervisor console, e.g. "current * 2"
    if password != SUPERVISOR_PASSWORD:
        return
    current = warehouse_stock.get(sku, 0)
    warehouse_stock[sku] = simple_eval(formula, names={"current": current})
    with open(AUDIT_FILE, "a", encoding="utf-8") as audit:
        audit.write("adjusted " + str(sku) +
                    " using formula " + formula + " at " +
                    str(datetime.now()) + "\n")


def main():
    """The main function"""
    add_stock("WID-001", 40)
    add_stock("WID-002", -4)
    add_stock(404, 15)  # invalid SKU type, no check
    remove_stock("WID-001", 12)
    remove_stock("GHOST-9", 1)
    remove_stock("WID-001", 500)
    print("WID-002 stock:", get_stock("WID-002"))
    print("Needs reorder:", check_reorder())
    apply_adjustment("WID-002", "current + 25", "wh-admin-1234")
    save_stock()
    load_stock()
    print_report()
    print('stock audit complete')  # dangerous


main()
