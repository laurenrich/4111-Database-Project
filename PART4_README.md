# Project Part 4: Database Schema Expansion

## Team Information
- **Team Member 1 Name:** Jolene Wang
- **Team Member 1 UNI:** jwc2239
- **Team Member 2 Name:** Lauren Rich
- **Team Member 2 UNI:** lar2250
- **PostgreSQL Account (UNI):** jwc2239

---

## Full Text Search

We implemented full text search functionality on the existing comment column in the review table. The comment column was of type TEXT, so it was suitable for storing document-style text. We used a GIN index on the text search vector of the comment column and made sure at least 10 reviews were populated with detailed, paragraph-length text. This addition makes sense because reviews naturally contain document-style text when users write their feedback, and the full-text search allows semantic search capabilities which allows users to find reviews based on meaning rather than exact string matching. This is useful for analyzing customer feedback and identifying common themes in reviews.

---

## Array Attribute

We added an 'allergens TEXT[]' column to the existing dish table. This array stores the allergens that may be present in each dish, for example, 'dairy', 'gluten', 'peanuts', 'shellfish', 'eggs', 'soy'. This addition works well with the structure of our project because many dishes contain multiple allergens and an array is a natural way to store this. It also supports quick look up to find dishes with or without specific allergens, which is helpful for customers with diets or food allergies/dietary restrictions. This is very common and useful for customer service in a restaurant database system.

---

## Trigger

We created a trigger that automatically maintains the 'total_orders' count in the restaurant table. When a new order is inserted into the orders table, the trigger increments the 'total_orders' counter for the corresponding restaurant. This improves query performance by avoiding repeated COUNT(*) calculations when displaying order statistics.

**Note:** We added the 'total_orders' column to the restaurant table as part of this feature. The trigger automatically maintains this cached value whenever orders are added.

### Trigger Execution Example

**Event:** Inserting a new order for restaurant with ID 1

```sql
INSERT INTO orders (userid, restaurantid, totalprice)
VALUES (1, 1, 25.00)
```

The trigger automatically fires after the INSERT completes.

The trigger updates the restaurant table where the total_orders columns for restaurantid = 1 is incremented by 1.

**Database Modifications:**
- orders table: 1 new row inserted (the new order)
- restaurant table: total_orders column for restaurantid = 1 increases by 1

To verify the trigger worked, you can run:
```sql
SELECT restaurantid, name, total_orders 
FROM restaurant 
WHERE restaurantid = 1
```

The `total_orders` value should have increased by 1 compared to before the INSERT.

---

## Queries

### Query 1: Full-Text Search
**Purpose:** Find reviews that mention "fresh ingredients" OR "exceptional service" using full-text search capabilities.

**What it computes:** This query searches the `comment` column for reviews containing words related to "fresh ingredients" or "exceptional service". It uses PostgreSQL's `to_tsvector` and `to_tsquery` functions with the 'english' configuration. The results are ranked by relevance score using `ts_rank`, showing the most relevant reviews first.

**Query:**
```sql
SELECT 
    r.reviewid,
    r.rating,
    rest.name AS restaurant_name,
    ts_rank(to_tsvector('english', r.comment), 
            to_tsquery('english', 'fresh & ingredients | exceptional & service')) AS relevance_score,
    substring(r.comment, 1, 150) AS review_preview
FROM review r
LEFT JOIN restaurant rest ON r.restaurantid = rest.restaurantid
WHERE to_tsvector('english', r.comment) @@ to_tsquery('english', 'fresh & ingredients | exceptional & service')
ORDER BY relevance_score DESC;
```

---

### Query 2: Array Attribute - Accessing Array Elements
**Purpose:** Find dishes that contain dairy allergens and display the first allergen in the array.

**What it computes:** This query demonstrates array operations by using the `@>` (contains) operator to find dishes whose `allergens` array contains 'dairy', and accessing the first element of the array using `allergens[1]` (PostgreSQL uses 1-based indexing).

**Query:**
```sql
SELECT 
    d.dishid,
    d.name AS dish_name,
    d.allergens,
    d.allergens[1] AS primary_allergen,
    array_length(d.allergens, 1) AS num_allergens,
    r.name AS restaurant_name
FROM dish d
LEFT JOIN restaurant r ON d.restaurantid = r.restaurantid
WHERE d.allergens @> ARRAY['dairy']::TEXT[]
ORDER BY d.name;
```
