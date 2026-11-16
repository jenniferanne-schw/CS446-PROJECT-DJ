import json
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
import boto3

TABLE_NAME = "PriceMatchList"
BUCKET_NAME = "price-drop-logs-2111-dj"

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
table = dynamodb.Table(TABLE_NAME)


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

#scan
def run_price_check():
    items = table.scan().get("Items", [])
    deals_found = []

    for item in items:
        product_id = item["product_id"]
        name = item.get("item_name", product_id)
        url = item["api_url"]
        json_key = item["json_key"]
        target_price = float(item["target_price"])

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        current_price = float(data[json_key]["usd"])
        item["last_price"] = Decimal(str(current_price))

        table.update_item(
            Key={"product_id": product_id},
            UpdateExpression="SET last_price = :p",
            ExpressionAttributeValues={":p": Decimal(str(current_price))},
        )

        #update
        if current_price <= target_price:
            deal = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "product": name,
                "current_price": current_price,
                "target_price": target_price,
            }
            deals_found.append(deal)
            print(f"PRICE_DROP_FOUND: {name} is now ${current_price} (Target: ${target_price})")
        else:
            print(f"No deal yet for {name}: ${current_price} > Target ${target_price}")

    if deals_found:
        file_key = f"deals_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=json.dumps(deals_found, indent=2),
            ContentType="application/json",
        )

    return {"items": items, "deals_found": deals_found, "deals_count": len(deals_found)}


def lambda_handler(event, context):
    # http requests from the S3 web dashboard
    http_method = event.get("requestContext", {}).get("http", {}).get("method")

    if http_method == "GET":
        items = table.scan().get("Items", [])
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"items": items}, default=decimal_default),
        }

    if http_method == "POST":
        body = json.loads(event.get("body") or "{}")
        action = body.get("action", "check")

        if action == "add":
            coin_id = body["product_id"].strip().lower()
            table.put_item(
                Item={
                    "product_id": coin_id,
                    "item_name": body.get("item_name", coin_id.title()),
                    "api_url": f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd",
                    "json_key": coin_id,
                    "target_price": Decimal(str(body["target_price"])),
                    "last_price": Decimal("0"),
                }
            )
            items = table.scan().get("Items", [])
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Added", "items": items}, default=decimal_default),
            }

        result = run_price_check()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, default=decimal_default),
        }

    result = run_price_check()
    return {"statusCode": 200, "deals_count": result["deals_count"]}
