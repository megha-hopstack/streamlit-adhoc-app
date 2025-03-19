import datetime
import io
import pandas as pd
from bson.objectid import ObjectId
from dateutil import tz

# Import your database connections.
# (Assumes you have these objects defined in a separate module like db.py)
from db import north_america_database, south_east_database

# -------------------------------
# Tenant & Collection Setup
# -------------------------------
# Tenant setup (for example, for 'Vault')
tenants_collection = north_america_database["tenants"]
cursor = tenants_collection.find({}, {"_id": 1, "name": 1, "apiGateway": 1, "active": 1})
tenant_df = pd.DataFrame(list(cursor))
tenant_df.rename(columns={'_id': 'tenant'}, inplace=True)
tenant_df['tenant'] = tenant_df['tenant'].astype(str)
tenant_df = tenant_df[tenant_df['name'] == 'Vault']
tenant_id = tenant_df['tenant'].iloc[0]

# Define collection objects for reuse
south_east_order_collection = south_east_database["orders"]
south_east_orderlineitem_collection = south_east_database["orderlineitems"]
south_east_consignment_collection = south_east_database["consignments"]
south_east_batch_collection = south_east_database["batches"]

# -------------------------------
# Report Generation Functions
# -------------------------------
def generate_outbound_report(start_date, end_date):
    """
    Generate an outbound report (orders and order line items) within the provided dates.
    Returns Excel file bytes and a pandas DataFrame for preview.
    """
    # Define timezones
    saudi_tz = tz.gettz('Asia/Riyadh')
    utc_tz = tz.gettz('UTC')
    
    # Ensure the datetime objects have the Saudi timezone
    start_date = start_date.replace(tzinfo=saudi_tz)
    end_date = end_date.replace(tzinfo=saudi_tz)
    
    # Convert to UTC and then to ObjectId timestamps
    start_date_utc = start_date.astimezone(utc_tz)
    end_date_utc = end_date.astimezone(utc_tz)
    start_ts = int(start_date_utc.timestamp())
    end_ts = int(end_date_utc.timestamp())
    start_oid = ObjectId.from_datetime(datetime.datetime.utcfromtimestamp(start_ts))
    end_oid = ObjectId.from_datetime(datetime.datetime.utcfromtimestamp(end_ts))
    
    # Query orders
    orders_cursor = south_east_order_collection.find({
        "tenant": tenant_id,
        "_id": {"$gte": start_oid, "$lte": end_oid},
        "customer": "64fda3c3823ef77f92d0af36",
        "warehouse": "63f204af4730a6193c250f5c",
        "orderStatus": {"$ne": "CANCELLED"}
    })
    orders = list(orders_cursor)
    order_ids = [order['_id'] for order in orders]
    
    # Query order line items
    olis_cursor = south_east_orderlineitem_collection.find({
        "order": {"$in": order_ids}
    })
    order_line_items = list(olis_cursor)
    
    # Map order id to order details for fast lookup
    order_dict = {order['_id']: order for order in orders}
    
    data = []
    for oli in order_line_items:
        order_info = order_dict.get(oli['order'])
        if order_info:
            data.append([
                order_info.get('orderId'),
                order_info.get('createdAt'),
                oli.get('sku'),
                oli.get('lotId'),
                oli.get('quantity')
            ])
    
    df_outbound = pd.DataFrame(data, columns=['Order ID', 'Order Date', 'SKU', 'Lot ID', 'Quantity'])
    df_outbound['Order Date'] = pd.to_datetime(df_outbound['Order Date'], unit='ms').dt.date
    
    # Write DataFrame to an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_outbound.to_excel(writer, index=False, sheet_name='Outbound')
    return output.getvalue(), df_outbound

def generate_inbound_report(start_date, end_date):
    """
    Generate an inbound report (batches and consignments) within the provided dates.
    Returns Excel file bytes and a pandas DataFrame for preview.
    """
    saudi_tz = tz.gettz('Asia/Riyadh')
    utc_tz = tz.gettz('UTC')
    
    start_date = start_date.replace(tzinfo=saudi_tz)
    end_date = end_date.replace(tzinfo=saudi_tz)
    
    start_date_utc = start_date.astimezone(utc_tz)
    end_date_utc = end_date.astimezone(utc_tz)
    start_ts = int(start_date_utc.timestamp())
    end_ts = int(end_date_utc.timestamp())
    start_oid = ObjectId.from_datetime(datetime.datetime.utcfromtimestamp(start_ts))
    end_oid = ObjectId.from_datetime(datetime.datetime.utcfromtimestamp(end_ts))
    
    # Helper to convert consignmentId string to ObjectId
    def convert_id(hex_str):
        return ObjectId(hex_str)
    
    batches_cursor = south_east_batch_collection.find({
        "tenant": tenant_id,
        "_id": {"$gte": start_oid, "$lte": end_oid},
        "customer": "64fda3c3823ef77f92d0af36",
        "warehouse": "63f204af4730a6193c250f5c",
        "typeOfBatch": "RECEIVING",
        "status": {"$in": ["COMPLETED", "PUTAWAY_STARTED", "PUTAWAY_COMPLETED"]},
        "consignmentId": {"$ne": None},
        "warehouse": "63f204af4730a6193c250f5c"
    })
    batches = list(batches_cursor)
    
    consignment_ids = [convert_id(batch["consignmentId"]) for batch in batches]
    
    consignments_cursor = south_east_consignment_collection.find({
        "_id": {"$in": consignment_ids},
        "tenant": tenant_id,
        "customer": "64fda3c3823ef77f92d0af36",
        "warehouse": "63f204af4730a6193c250f5c"
    })
    consignments = list(consignments_cursor)
    consignment_dict = {str(consignment['_id']): consignment for consignment in consignments}
    
    data = []
    for batch in batches:
        consignment = consignment_dict.get(str(batch["consignmentId"]))
        if consignment:
            data.append([
                consignment.get('orderId'),
                batch.get('createdAt'),
                batch.get('sku'),
                batch.get('lotId'),
                batch.get('quantity')
            ])
    
    df_inbound = pd.DataFrame(data, columns=['Order ID', 'Date', 'SKU', 'Lot ID', 'Quantity'])
    df_inbound['Date'] = pd.to_datetime(df_inbound['Date'], unit='ms').dt.date
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_inbound.to_excel(writer, index=False, sheet_name='Inbound')
    return output.getvalue(), df_inbound
