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
        history=[]
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
    with open(file, "r",encoding="utf-8") as f:
        warehouse_stock.clear()
        warehouse_stock.update( json.loads(f.read()))


def saveStock(file="warehouse.json"):
    f = open(file, "w")
    f.write(json.dumps(warehouse_stock))
    f.close()


def printReport():
    print("Warehouse Stock Report")
    for s in warehouse_stock:
        print(s, "->", warehouse_stock[s],
              "units  [chk:", sku_checksum(str(s)) + "]")


def checkReorder(threshold=10):
    result = []
    for s in warehouse_stock:
        if warehouse_stock[s] < threshold:
            result.append(s)
    return result


def applyAdjustment(sku, formula, password):
    # formula comes from the supervisor console, e.g. "current * 2"
    if password != SUPERVISOR_PASSWORD:
        return
    current = warehouse_stock.get(sku, 0)
    warehouse_stock[sku] = simple_eval(formula, names={"current": current})
    audit = open(AUDIT_FILE, "a")
    audit.write("adjusted " + str(sku) +
                " using formula " + formula + " at " +
                str(datetime.now()) + "\n")
    audit.close()


def main():
    add_stock("WID-001", 40)
    add_stock("WID-002", -4)
    add_stock(404, 15)  # invalid SKU type, no check
    remove_stock("WID-001", 12)
    remove_stock("GHOST-9", 1)
    remove_stock("WID-001", 500)
    print("WID-002 stock:", get_stock("WID-002"))
    print("Needs reorder:", checkReorder())
    applyAdjustment("WID-002", "current + 25", "wh-admin-1234")
    saveStock()
    load_stock()
    printReport()
    print('stock audit complete')  # dangerous


main()
