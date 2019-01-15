# Shopify developer challenge
## Online marketplace API
This is a simple API for an online marketplace, built using Python Flask web microframework. You can test the hosted version available at https://opendata.website but the server is slow, so I recommend running it locally.

## Get started
In order to run the API locally, you need the Python 3.x.x with the following dependencies installed:
* flask
* flask-limiter
* sqlite3
* datetime

You can install them via `pip install`.

## Routes

|Endpoint                    |GET|POST|PUT|DELETE|
|----------------------------|-----------|-----------|----------|------|
| /api/products              | Query all products from the database. You can also query only available products by adding `?available=True` or `?available=1` parameter.| Add a new product to the database. The request should look like this: `{'title': 'Product's title, 'price': 399.99, 'quantity': 10}`|-|Delete all existing products from the database.
| /api/products/1            | Query a product with Id of 1.|-|Update the product's details. The request should look like the POST request to create a new product except non of the fields are required. E.g you can update price only: `{'price': 459.86}`|Delete the product with an Id of 1.
| /api/products/1/purchase   |-| Purchase a product with Id of 1. `inventory_count` will be decresed in the database. If a product is unavailable you will get 404 `Product out of stock` response.|-|-
| /api/cart/1                | Query all data about a cart with Id of 1. That means all products added to the cart, their prices, quantities and total price.| Create a new cart with Id of 1 (if doesn't exist) and add a specified product to it. Example request: `{'product_id': 1, 'quantity': 2}`|-|Remove specific product from the cart.
| /api/cart/1/complete       |-|"Complete" the cart with Id of 1. This means that the inventory of each added product will be reduced.|-|-


## Examples of each request
`curl -d '{"title": "PearBook 15 inches", "price": 1699.99, "inventory_count": 20}' -H "Content-Type: application/json" -X POST https://opendata.website/api/products`\
Output:
```
{
  "created_resource": "/api/products/1"
}
```
--------------------------------------------------------------------
`curl --request GET http://opendata.website/api/products/1`\
Output:
```
{
  "product_id": 1, 
  "title": "PearBook 15 inches", 
  "price": 1699.99, 
  "inventory_count": 20
}
```
--------------------------------------------------------------------
`curl --request GET http://opendata.website/api/products`\
Output:
```
[
  {
    "product_id": 1, 
    "title": "PearBook 15 inches", 
    "price": 1699.99, 
    "inventory_count": 20
  }, 
  {
    "product_id": 2, 
    "title": "PearPhone 32gb", 
    "price": 799.99, 
    "inventory_count": 27
  }, 
  {
    "product_id": 3, 
    "title": "PearPhone 64gb", 
    "price": 899.99, 
    "inventory_count": 0
  }
]
```
--------------------------------------------------------------------
`curl --request GET http://opendata.website/api/products?available=true`\
Output:
```
[
  {
    "product_id": 1, 
    "title": "PearBook 15 inches", 
    "price": 1699.99, 
    "inventory_count": 20
  }, 
  {
    "product_id": 2, 
    "title": "PearPhone 32gb", 
    "price": 799.99, 
    "inventory_count": 27
  }
]
```
--------------------------------------------------------------------
`curl -d '{"price": 449.87}' -H "Content-Type: application/json" -X PUT https://opendata.website/api/products/1`\
Output:
```
Updated
```
--------------------------------------------------------------------
`curl --request DELETE http://opendata.website/api/products/1`\
Output:
```
Deleted
```
--------------------------------------------------------------------
`curl --request DELETE http://opendata.website/api/products`\
Output:
```
"Deleted"
```
--------------------------------------------------------------------
`curl --request POST http://opendata.website/api/products/1/purchase`\
Output:
```
"Purchased"
```
--------------------------------------------------------------------
`curl -d '{"product_id": 1, "quantity": 2}' -H "Content-Type: application/json" -X POST https://opendata.website/api/cart/1`\
Output:
```
{
  "total": 899.74, 
  "products": [
    {
      "product_id": 1, 
      "title": "PearBook 15 inches", 
      "price": 449.87, 
      "total": 899.74, 
      "quantity": 2
    }
  ]
}
```
--------------------------------------------------------------------
`curl --request POST http://opendata.website/api/cart/1/complete`\
Output:
```
"Cart 1 completed"
```
--------------------------------------------------------------------
`curl -d '{"product_id": 1}' -H "Content-Type: application/json" -X DELETE https://opendata.website/api/cart/1`\
Output:
```
"Deleted"
```
--------------------------------------------------------------------


### Security
Security is a significant aspect of every API. Here are the steps that have been made towards making this Online Marketplace API more secure:
1. Only requests over HTTPS are allowed.
2. Returns 405 `Method not allowed` if one is using method that is not allowed.
3. Returns 429 `Too many requests` if requests are coming too quickly.
4. All input data and/or parameters are validated.
5. The API doesn't show any details in case of server's internal error.
