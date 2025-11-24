# Project Part 4: Database Schema Expansion

## Team Information
- **Team Member 1 Name:** Jolene Wang
- **Team Member 1 UNI:** jwc2239
- **Team Member 2 Name:** Lauren Rich
- **Team Member 2 UNI:** lar2250
- **PostgreSQL Account (UNI):** jwc2239

---

## Full Text Search

**Schema Modification:** We enhanced the existing `comment` column in the `review` table to support full-text search capabilities. The column was already of type TEXT, making it suitable for document-style content.

**Implementation Details:**
- Created a GIN index on the text search vector: `CREATE INDEX idx_review_comment_fts ON review USING gin(to_tsvector('english', comment));`
- Populated at least 10 reviews with detailed, paragraph-length text containing natural language content
- Used PostgreSQL's built-in text search functions (`to_tsvector`, `to_tsquery`, `ts_rank`)

**Rationale:** This addition integrates naturally with our restaurant database because customer reviews inherently contain document-style text with rich semantic content. Full-text search enables semantic search capabilities beyond exact string matching, ranking results by relevance, advanced query capabilities with boolean operators, and efficient searching through large volumes of review text. This feature is valuable for restaurant owners to analyze customer feedback, identify common themes, and understand customer sentiment patterns.

---

## Array Attribute

**Schema Modification:** We added an `allergens TEXT[]` column to the existing `dish` table using `ALTER TABLE dish ADD COLUMN allergens TEXT[];`

**Implementation Details:**
- Array stores multiple allergen values per dish (e.g., `{'dairy', 'gluten', 'nuts'}`)
- Updated all existing dishes with appropriate allergen arrays
- Common allergens include: 'dairy', 'gluten', 'peanuts', 'tree nuts', 'shellfish', 'fish', 'eggs', 'soy', 'sesame'
- Each dish has 0-5 allergens based on realistic ingredient combinations

**Rationale:** This modification fits perfectly within our restaurant database structure because dishes naturally contain multiple allergens, making arrays the ideal data structure. It avoids creating separate allergen tables, enables efficient queries using array operators, supports critical functionality for customers with dietary restrictions, allows restaurants to quickly filter menu items based on allergen requirements, and facilitates compliance with food safety regulations requiring allergen disclosure.

---

## Trigger

**Schema Modification:** We implemented a trigger system to automatically maintain order statistics by adding `total_orders INTEGER DEFAULT 0` column to the `restaurant` table, creating a PL/pgSQL function, and creating an AFTER INSERT trigger on the `orders` table.

**Implementation Details:**
```sql
ALTER TABLE restaurant ADD COLUMN total_orders INTEGER DEFAULT 0;

CREATE OR REPLACE FUNCTION update_restaurant_order_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE restaurant 
    SET total_orders = total_orders + 1 
    WHERE restaurantid = NEW.restaurantid;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_order_count
    AFTER INSERT ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_restaurant_order_count();
```

**Rationale:** This trigger provides performance optimization by eliminating expensive COUNT(*) operations, ensures data consistency by automatically maintaining accurate order counts, enables real-time updates when new orders are placed, supports business intelligence for restaurant popularity analysis, and maintains scalability with constant-time access to order counts regardless of database size.

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

---

### Query 3: Trigger Functionality
**Purpose:** Display restaurants with their cached total_orders count maintained by the trigger.

**What it computes:** This query shows how the trigger maintains the `total_orders` column by displaying restaurants along with their automatically-updated order counts. The `total_orders` value is kept current by the trigger whenever new orders are inserted.

**Query:**
```sql
SELECT 
    r.restaurantid,
    r.name AS restaurant_name,
    r.total_orders,
    r.location,
    r.pricerange
FROM restaurant r
WHERE r.total_orders > 0
ORDER BY r.total_orders DESC;
```
