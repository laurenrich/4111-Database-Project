# Project Part 4: Database Schema Expansion

## Team Information
- **Team Member 1 Name:** Jolene Wang
- **Team Member 1 UNI:** jwc2239
- **Team Member 2 Name:** Lauren Rich
- **Team Member 2 UNI:** lar2250
- **PostgreSQL Account (UNI):** jwc2239

---

## Overview

This document describes the expansion of our Project Part 3 database schema with three advanced PostgreSQL features:
1. **Full-Text Search** - Added full-text search capability to the `review.comment` column
2. **Array Attribute** - Added `allergens TEXT[]` array column to the `dish` table
3. **Trigger** - Created a trigger to automatically maintain `total_orders` count in the `restaurant` table

---

## 1. Full-Text Search Feature

### Rationale and Design

We implemented full-text search functionality on the existing `comment` column in the `review` table. The `comment` column was of type TEXT, so it was suitable for storing document-style text. We used a GIN index on the text search vector of the comment column and made sure at least 10 reviews were populated with detailed, paragraph-length text.

This addition makes sense because reviews naturally contain document-style text when users write their feedback, and the full-text search allows semantic search capabilities which allows users to find reviews based on meaning rather than exact string matching. This is useful for analyzing customer feedback and identifying common themes in reviews.

### Implementation

```sql
CREATE INDEX idx_review_comment_fulltext 
ON review USING gin(to_tsvector('english', comment));
```

We updated at least 10 existing reviews with detailed paragraph-length text describing dining experiences, food quality, service, atmosphere, and recommendations.

### How It Fits Within the Project

Full-text search enhances the review system by allowing users and administrators to search through reviews using natural language queries. For example, they can find all reviews mentioning "exceptional service" or "fresh ingredients" without needing exact keyword matches. This is particularly useful for analyzing customer feedback and identifying common themes in reviews.

---

## 2. Array Attribute Feature

### Rationale and Design

We added an `allergens TEXT[]` column to the existing `dish` table. This array stores the allergens that may be present in each dish, for example, 'dairy', 'gluten', 'peanuts', 'shellfish', 'eggs', 'soy'.

This addition works well with the structure of our project because many dishes contain multiple allergens and an array is a natural way to store this. It also supports quick look up to find dishes with or without specific allergens, which is helpful for customers with diets or food allergies/dietary restrictions. This is very common and useful for customer service in a restaurant database system.

### Implementation

```sql
ALTER TABLE dish ADD COLUMN allergens TEXT[];

CREATE INDEX idx_dish_allergens ON dish USING gin(allergens);
```

We populated the `allergens` column with meaningful arrays for at least 10 dishes. Each array contains relevant allergens such as:
- `ARRAY['dairy', 'gluten']` for pasta dishes with cream sauce
- `ARRAY['peanuts', 'soy']` for Asian dishes
- `ARRAY['gluten', 'eggs', 'dairy']` for breaded items
- `ARRAY[]::TEXT[]` for allergen-free dishes (empty array)

### How It Fits Within the Project

The allergens array supports critical functionality for customers with food allergies or dietary restrictions. Users can quickly find dishes that are safe for their dietary needs, and restaurants can efficiently manage allergen information. This is essential for food safety and customer service in a restaurant database system.

---

## 3. Trigger Feature

### Rationale and Design

We created a trigger that automatically maintains the `total_orders` count in the `restaurant` table. When a new order is inserted into the `orders` table, the trigger increments the `total_orders` counter for the corresponding restaurant. This improves query performance by avoiding repeated COUNT(*) calculations when displaying order statistics.

**Note:** We added the `total_orders` column to the `restaurant` table as part of this feature. The trigger automatically maintains this cached value whenever orders are added.

### Implementation

```sql
-- Add column
ALTER TABLE restaurant ADD COLUMN total_orders INTEGER DEFAULT 0;

-- Create function
CREATE OR REPLACE FUNCTION increment_order_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE restaurant 
    SET total_orders = total_orders + 1 
    WHERE restaurantid = NEW.restaurantid;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_increment_order_count
AFTER INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION increment_order_count();
```

### What the Trigger Achieves

The trigger automatically maintains an accurate count of total orders for each restaurant. This eliminates the need to calculate `COUNT(*)` from the `orders` table every time order statistics are needed, improving query performance and ensuring the count is always up-to-date.

### Trigger Execution Example

**Event:** Inserting a new order for restaurant with ID 1

**Step 1:** Execute the following INSERT statement:
```sql
INSERT INTO orders (userid, restaurantid, totalprice) 
VALUES (1, 1, 25.00);
```

**Step 2:** The INSERT operation completes, adding a new row to the `orders` table.

**Step 3:** The trigger `trigger_increment_order_count` automatically fires AFTER the INSERT completes.

**Step 4:** The trigger function executes and updates the `restaurant` table:
- Finds the restaurant with `restaurantid = 1`
- Increments the `total_orders` column by 1
- If `total_orders` was previously 5, it becomes 6

**Database Modifications:**
- **orders table:** 1 new row inserted (the new order)
- **restaurant table:** `total_orders` column for restaurantid = 1 increases by 1

**Verification:**
To verify the trigger worked, you can run:
```sql
SELECT restaurantid, name, total_orders 
FROM restaurant 
WHERE restaurantid = 1;
```
The `total_orders` value should have increased by 1 compared to before the INSERT.

---

## Queries

### Query 1: Full-Text Search
**Purpose:** Find reviews that mention "fresh ingredients" OR "exceptional service" using full-text search capabilities.

**What it computes:** This query searches the `comment` column for reviews containing words related to "fresh ingredients" or "exceptional service". It uses PostgreSQL's `to_tsvector` and `to_tsquery` functions with the 'english' configuration. The results are ranked by relevance score using `ts_rank`, showing the most relevant reviews first. The query demonstrates full-text search by using the `@@` operator to match text search vectors against queries, and the `|` (OR) operator to search for multiple related terms.

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

**What it computes:** This query demonstrates array operations by:
1. Using the `@>` (contains) operator to find dishes whose `allergens` array contains 'dairy'
2. Accessing the first element of the array using `allergens[1]` (PostgreSQL uses 1-based indexing)
3. Using `array_length` to show how many allergens each dish has
4. Displaying the full array and individual elements

This query shows how to access specific elements within arrays, which is a key requirement for array attribute queries.

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

---

## Summary

Our schema expansion successfully integrates three advanced PostgreSQL features into our restaurant database:

1. **Full-text search** enables semantic search through detailed reviews, improving the user experience for finding relevant restaurant feedback based on meaning rather than exact keywords.

2. **Array attributes** efficiently model multi-valued allergen data, supporting important dietary restriction queries and food safety requirements.

3. **Triggers** automatically maintain data consistency by caching calculated values (order counts), improving query performance and ensuring accuracy without manual intervention.

All features are meaningfully integrated into the existing schema and enhance the database's functionality for real-world restaurant management and customer service scenarios.

