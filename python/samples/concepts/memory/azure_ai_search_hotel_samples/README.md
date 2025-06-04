## Azure AI Search with Hotel Sample Data

This guide walks you through setting up your Azure AI Search Service with the correct index, data source, and indexer to run the hotel sample.

### Setting Up the Azure AI Search Service

1. **Import the Sample Data**  
   - Navigate to the **Search Service Overview** page and click **Import Data**.
   - From the dropdown, select **Samples**, then choose **hotels-sample**.
   - Click **Next: Add Cognitive Skills (Optional)**.

2. **Skip the Cognitive Skills Page**  
   - No changes are needed here. Click **Next** to proceed.

3. **Configure the Index Fields**  
   - The Python sample uses **snake_case** field names. Update the default field names accordingly.
   - Since `HotelId` is the primary key, you cannot rename it directly. Instead, create a new field:
     - Click **+ Add Field** and name it `hotel_id`.
     - Enable **Retrievable**, **Filterable**, **Facetable**, and **Searchable** options.
   - Rename other fields to snake case:
     - `HotelName` → `hotel_name`
       - There may be a current issue with index config that has trouble mapping the `HotelName` -> `hotel_name`, so as to not hit issues
         deselect `retrievable` for `hotel_name`. It should still be `searchable`.
     - Use the dropdown to rename complex fields like `Address` -> `address` and `Rooms` -> `rooms` with their sub-fields renamed.
   - Add two new vector fields:
     - `description_vector`
     - `description_fr_vector`
   - Configure these fields as:
     - **Type**: `Collection(Edm.Single)` (for vector fields)
     - **Retrievable**: Enabled (default setting)
     - Click the **three dots (...)** on the right, then **Configure vector field**:
       - Set **Dimensions** to `1536`.
       - If no vector search profiles exist, click **Create**.
       - Under **Algorithms**, click **Create** to set up a vector algorithm (default values are fine).
       - If no vectorizer exists, create one:
         - Select the **Kind** (e.g., Azure OpenAI).
         - Choose your **subscription, Azure OpenAI service, and model deployment**.
         - Select your **authentication type**.
   - Repeat this process for both `description_vector` and `description_fr_vector`.

4. **Create an Indexer**  
   - On the next page, create an indexer with **default settings**, as the sample data is static.
   - Click **Submit** to start the indexer.  
   - The indexing process may take a few minutes.

### Generating Vectors on First Run

In the `step_1_interact_with_the_collection.py` script:
- Set `first_run = True` to generate vectors for all entries in the index.
- This process may take a few minutes.

### Using Precomputed Vectors for Subsequent Runs

If your index already contains vectors:
- Set `first_run = False` to skip vector generation and perform only text and vector searches.

### Example Search Results

After running `step_1_interact_with_the_collection.py` you should see output similar to:

#### **Text Search Results**
```text
Search results using text: 
    eitRUkFJSmFmWG93QUFBQUFBQUFBQT090 (in Nashville, USA): All of the suites feature full-sized kitchens stocked with cookware, separate living and sleeping areas and sofa beds. Some of the larger rooms have fireplaces and patios or balconies. Experience real country hospitality in the heart of bustling Nashville. The most vibrant music scene in the world is just outside your front door. (score: 7.613796)
    eitRUkFJSmFmWG9jQUFBQUFBQUFBQT090 (in Sarasota, USA): The hotel is situated in a nineteenth century plaza, which has been expanded and renovated to the highest architectural standards to create a modern, functional and first-class hotel in which art and unique historical elements coexist with the most modern comforts. The hotel also regularly hosts events like wine tastings, beer dinners, and live music. (score: 6.1204605)
    eitRUkFJSmFmWG9SQUFBQUFBQUFBQT090 (in Durham, USA): Save up to 50% off traditional hotels. Free WiFi, great location near downtown, full kitchen, washer & dryer, 24/7 support, bowling alley, fitness center and more. (score: 6.0284567)

Search results using vector: 
    eitRUkFJSmFmWG93QUFBQUFBQUFBQT090 (in Nashville, USA): All of the suites feature full-sized kitchens stocked with cookware, separate living and sleeping areas and sofa beds. Some of the larger rooms have fireplaces and patios or balconies. Experience real country hospitality in the heart of bustling Nashville. The most vibrant music scene in the world is just outside your front door. (score: 0.6944429)
    eitRUkFJSmFmWG9SQUFBQUFBQUFBQT090 (in Durham, USA): Save up to 50% off traditional hotels. Free WiFi, great location near downtown, full kitchen, washer & dryer, 24/7 support, bowling alley, fitness center and more. (score: 0.6776492)
    eitRUkFJSmFmWG9PQUFBQUFBQUFBQT090 (in San Diego, USA): Extend Your Stay. Affordable home away from home, with amenities like free Wi-Fi, full kitchen, and convenient laundry service. (score: 0.67669696)
```