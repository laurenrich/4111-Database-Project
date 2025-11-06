# Restaurant Database Web Application

## Database Information
**PostgreSQL Account:** jcw2239

## Web Application URL
**URL:** http://127.0.0.1:8111

**Note:** To test admin functionality and sample customer functionality:
- **Admin:** lar2250 / passwordfisijc
- **Customer:** jcw2239 / password12324

## Implementation Summary

### Parts of Original Proposal Implemented

**Core Database Entities (Fully Implemented):**
- Restaurant with attributes RestaurantID, Name, Location, Price Range
- Dish with attributes DishID, Name, Ingredients, Price (linked to Restaurant)
- User with attributes UserID, Name, Username, Password, Role
- Order with attributes OrderID, Date, TotalPrice (linked to User, Restaurant)
- Review with attributes ReviewID, Rating, Comment (linked to Restaurant and User)
- Cuisine with attributes CuisineID, CuisineName
- OrderItem junction table linking Orders to Dishes with quantity and price

**Core Relationships (Fully Implemented):**
- Restaurant has Dish
- User places Order
- User writes Review
- Order contains Dish (via OrderItem)
- Review rates Restaurant
- Restaurant serves Cuisine (via RestaurantCuisine junction table)

**User Roles (Fully Implemented):**
- **Customer:** Can create accounts, place orders, write reviews. All data is user-specific.
- **Admin:** Can add/update/delete restaurants, dishes, and reviews. Has full CRUD capabilities.

**Core Functionality (Fully Implemented):**
- User registration and authentication system
- Restaurant directory with search and filtering (by cuisine, price range, location)
- Restaurant detail pages showing dishes, reviews, cuisines, and orders
- Order placement system with dish selection and quantity
- Review system with star ratings and comments
- Role-based access control

**Enhanced Search and Filtering (Fully Implemented):**
- Dynamic restaurant search with multiple filter criteria
- Real-time filtering by cuisine, price range, and location
- Case-insensitive text search with ILIKE operations
- Dropdown filters populated from database

**Shopping Cart Functionality (Fully Implemented):**
- Order editing capability allowing customers to modify existing orders
- Real-time quantity adjustments with automatic total calculation
- Add/remove dishes from existing orders
- Interactive JavaScript-based price calculation
- Transaction-safe order updates with proper rollback handling

### Parts Not Implemented

**Enhanced UI Features:**
- Restaurant result cards with average ratings and "View Menu" buttons
- Interactive maps showing restaurant locations

**Reason:** We focused on core database functionality and CRUD operations rather than advanced UI enhancements. The current implementation provides all essential features for demonstration purposes.

**Advanced Admin Tools:**
- Bulk CSV upload for dishes
- Sorting and pagination features

**Reason:** These features would require additional file handling and complex UI components that were beyond the scope of our core database demonstration. The current admin tools provide sufficient CRUD functionality.

**Recommendation System:**
- Restaurant recommendations based on user preferences and ratings

**Reason:** This would require complex algorithms and machine learning components that were outside the scope of a database-focused project. Our focus was on demonstrating proper database design and operations.

### Additional Features Implemented

**Delete Functionality:**
- Admin users can delete restaurants, dishes, and reviews
- Proper confirmation dialogs and error handling
- Cascading delete behavior for related data

**User-Specific Data Views:**
- Orders page shows only the logged-in user's orders
- Reviews page shows only the logged-in user's reviews
- Enhanced privacy and data security

**User Registration System:**
- Complete user account creation with form validation
- Password length requirements (minimum 8 characters)
- Username uniqueness checking
- Automatic customer role assignment
- Secure authentication and session management

### Data Source Decision

**Original Plan:** Use Yelp Open Dataset for real restaurant information.

**Actual Implementation:** Used custom-generated sample data.

**Reason:** We decided to use our own sample data to maintain better control over the demonstration environment and ensure data consistency for testing purposes. This approach allowed us to create specific test cases and scenarios that showcase all database features effectively. For a production system, integrating real data from Yelp would be a natural extension, but for educational and demonstration purposes, our custom dataset provides better clarity and control.

## Most Interesting Database Operations

### 1. Restaurant Search and Filtering Page (`/restaurants`)

**Purpose:** Allows users to search and filter restaurants by multiple criteria simultaneously.

**Database Operations:**
- Dynamic SQL query construction based on user input
- Multiple JOIN operations between Restaurant, RestaurantCuisine, and Cuisine tables
- ILIKE operations for case-insensitive text search
- Exact matching for dropdown filters (cuisine, price range, location)
- Distinct queries to populate filter dropdown options

**Why Interesting:** This page demonstrates complex query building where the SQL is constructed dynamically based on user input. The system handles optional parameters gracefully, building different WHERE clauses depending on which filters are applied. It showcases how to efficiently combine text search with categorical filtering while maintaining good performance through proper indexing on foreign keys.

### 2. Order Creation Page (`/restaurants/<id>/add-order`)

**Purpose:** Allows users to create orders by selecting multiple dishes with quantities and calculates total pricing.

**Database Operations:**
- Transaction management across multiple tables (Orders and OrderItem)
- Price calculation and preservation at order time
- Foreign key validation for User, Restaurant, and Dish entities
- Batch insertion of order items with individual pricing
- Real-time price lookup from Dish table to ensure current pricing

**Why Interesting:** This page demonstrates complex transaction handling where data integrity is critical. The system must ensure that if any part of the order creation fails, the entire transaction is rolled back. It also showcases how to handle many-to-many relationships (Order-Dish via OrderItem) with additional attributes (quantity, price). The price preservation feature ensures that orders maintain historical pricing even if dish prices change later, which is crucial for business applications.

Both pages demonstrate sophisticated database operations that go beyond simple CRUD, involving complex queries, transaction management, and real-world business logic implementation.