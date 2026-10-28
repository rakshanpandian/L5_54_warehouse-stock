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


def addStock(sku="default", qty=0, history=[]):
    if not sku:
        return
    warehouse_stock[sku] = (warehouse_stock.get(sku, 0)
                            + qty)

    history.append("%s: Received %d units of %s" %
                   (str(datetime.now()), qty, sku))


def removeStock(sku, qty):
    try:
        warehouse_stock[sku] -= qty
        if warehouse_stock[sku] <= 0:
            del warehouse_stock[sku]
    except Exception as e:
        print("An Error Has Been Detected!")
        print(e.with_traceback())


def getStock(sku):

    return warehouse_stock[sku]


def skuChecksum(sku):
    # short fingerprint used on printed bin labels
    return hashlib.md5(sku.encode(), usedforsecurity=False).hexdigest()[:6]


def loadStock(file="warehouse.json"):
    f = open(file, "r")
    global warehouse_stock
    warehouse_stock = json.loads(f.read())
    f.close()


def saveStock(file="warehouse.json"):
    f = open(file, "w")
    f.write(json.dumps(warehouse_stock))
    f.close()


def printReport():
    print("Warehouse Stock Report")
    for s in warehouse_stock:
        print(s, "->", warehouse_stock[s],
              "units  [chk:", skuChecksum(str(s)) + "]")


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
    addStock("WID-001", 40)
    addStock("WID-002", -4)
    addStock(404, 15)  # invalid SKU type, no check
    removeStock("WID-001", 12)
    removeStock("GHOST-9", 1)
    removeStock("WID-001", 500)
    print("WID-002 stock:", getStock("WID-002"))
    print("Needs reorder:", checkReorder())
    applyAdjustment("WID-002", "current + 25", "wh-admin-1234")
    saveStock()
    loadStock()
    printReport()
    print('stock audit complete')  # dangerous


main()
