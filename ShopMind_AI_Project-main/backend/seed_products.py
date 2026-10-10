import asyncio,json,os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
load_dotenv()
async def main():
    client=AsyncIOMotorClient(os.getenv("MONGODB_URI","mongodb://localhost:27017"))
    db=client[os.getenv("MONGODB_DATABASE","shopmind")]
    products=json.loads(Path("sample_products.json").read_text(encoding="utf-8"))
    for p in products: await db.products.update_one({"product_id":p["product_id"]},{"$set":p},upsert=True)
    print(f"Seeded {len(products)} illustrative products into {db.name}.products")
    client.close()
if __name__=="__main__": asyncio.run(main())
