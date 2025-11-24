# Project Part 4: Database Schema Expansion

## Team Information
- **Team Member 1 Name:** Jolene Wang
- **Team Member 1 UNI:** jwc2239
- **Team Member 2 Name:** Lauren Rich
- **Team Member 2 UNI:** lar2250
- **PostgreSQL Account (UNI):** jwc2239

All three features described below were not present in our Part 3 schema and are new additions for Part 4 as required.

---

## Schema Objects Added

- GIN index `idx_review_comment_fts` on review(comment)
- New column `dish.allergens TEXT[]`
- New column `restaurant.total_orders INTEGER DEFAULT 0`
- Trigger function `update_restaurant_order_count()`
- Trigger `trigger_update_order_count` on orders

---

## Full Text Search

**Schema Modification:** We added a new `description TEXT` column to the `restaurant` table using `ALTER TABLE restaurant ADD COLUMN description TEXT;` to support full-text search capabilities on document-style content.

**Implementation Details:**
- Created a GIN index on the text search vector: `CREATE INDEX idx_restaurant_description_fulltext ON restaurant USING gin(to_tsvector('english', description));`
- Populated at least 10 restaurants with detailed, paragraph-length descriptions containing natural language content about each restaurant's history, ambiance, specialties, and dining experience
- Used PostgreSQL's built-in text search functions (`to_tsvector`, `to_tsquery`, `ts_rank`)

**Rationale:** This addition integrates naturally with our restaurant database because restaurant descriptions inherently contain document-style text with rich semantic content about cuisine, atmosphere, service quality, and dining experience. Full-text search enables semantic search capabilities beyond exact string matching, ranking results by relevance, advanced query capabilities with boolean operators, and efficient searching through large volumes of descriptive text. This feature is valuable for users to find restaurants based on specific characteristics like "authentic Italian" or "fresh ingredients" or "romantic atmosphere", helping them discover restaurants that match their preferences and dining needs.

Ten reviews in our live database have been updated with paragraph-length comment text to support full-text search.

---

## Array Attribute

**Schema Modification:** We added an `allergens TEXT[]` column to the existing `dish` table using `ALTER TABLE dish ADD COLUMN allergens TEXT[];`

**Implementation Details:**
- Array stores multiple allergen values per dish (e.g., `{'dairy', 'gluten', 'nuts'}`)
- Updated all existing dishes with appropriate allergen arrays
- Common allergens include: 'dairy', 'gluten', 'peanuts', 'tree nuts', 'shellfish', 'fish', 'eggs', 'soy', 'sesame'
- Each dish has 0-5 allergens based on realistic ingredient combinations

**Rationale:** This modification fits perfectly within our restaurant database structure because dishes naturally contain multiple allergens, making arrays the ideal data structure. It avoids creating separate allergen tables, enables efficient queries using array operators, supports critical functionality for customers with dietary restrictions, allows restaurants to quickly filter menu items based on allergen requirements, and facilitates compliance with food safety regulations requiring allergen disclosure.

Ten dishes in our live database have been updated with meaningful allergen arrays.

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
**Purpose:** Find restaurants that mention "authentic" OR "fresh" OR "traditional" in their descriptions using full-text search capabilities.

**What it computes:** This query searches the `description` column for restaurants containing words related to "authentic", "fresh", or "traditional". It uses PostgreSQL's `to_tsvector` and `to_tsquery` functions with the 'english' configuration. The results are ranked by relevance score using `ts_rank`, showing the most relevant restaurants first.

**Query:**
```sql
SELECT 
    restaurantid,
    name AS restaurant_name,
    ts_rank(to_tsvector('english', description), 
            to_tsquery('english', 'authentic | fresh | traditional')) AS relevance_score,
    substring(description, 1, 150) AS description_preview
FROM restaurant
WHERE to_tsvector('english', description) @@ to_tsquery('english', 'authentic | fresh | traditional')
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
