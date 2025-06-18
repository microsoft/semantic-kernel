## Azure AI Search with Hotel Sample Data

This guide explains how to use the provided Python samples to set up your Azure AI Search index, load hotel data, and run search queries—all programmatically, without manual configuration in the Azure Portal.

### Overview

The Python samples in this folder will:

- Define the hotel data model and index schema.
- Download and load the hotel sample data.
- Create the Azure AI Search index (if it does not exist).
- Upsert the data into your Azure AI Search index.
- Run text, vector, and hybrid search queries.

### Prerequisites

- An Azure AI Search service instance.
- OpenAI resource (for embedding generation), can be replaced with Azure OpenAI Embeddings.

### How It Works

1. **Data Model and Index Creation**  
   The data model and index schema are defined in `data_model.py`.  
   This script is called by the other two, so no need to run manually.

2. **Loading Data and Generating Vectors**  
   The script downloads hotel data from the Azure samples repository.  
   It uses OpenAI to generate vector embeddings for hotel descriptions, which are stored in the index.

3. **Running the Sample**  
   To run the main sample and see search results:

   ```bash
   python 1_interact_with_the_collection.py
   ```

   This will:
   - Create the index (if needed)
   - Load and upsert the hotel data
   - Get the first five records
   - Perform vector and hybrid search queries and print the results

4. **Customizing the Search**  
   You can modify the search query in `1_interact_with_the_collection.py` by changing the `query` variable at the bottom of the script.

5. **Cleanup**  
   The sample script deletes the index at the end of execution. You can comment out this step if you want to keep the index for further experimentation.

### Example Output

```python
Get first five records: 
    31 (in Nashville, USA): All of the suites feature full-sized kitchens stocked with cookware, separate living and sleeping areas and sofa beds. Some of the larger rooms have fireplaces and patios or balconies. Experience real country hospitality in the heart of bustling Nashville. The most vibrant music scene in the world is just outside your front door.
    23 (in Kirkland, USA): Mix and mingle in the heart of the city. Shop and dine, mix and mingle in the heart of downtown, where fab lake views unite with a cheeky design.
    3 (in Atlanta, USA): The Gastronomic Hotel stands out for its culinary excellence under the management of William Dough, who advises on and oversees all of the Hotel’s restaurant services.
    20 (in Albuquerque, USA): The Best Gaming Resort in the area. With elegant rooms & suites, pool, cabanas, spa, brewery & world-class gaming. This is the best place to play, stay & dine.
    45 (in Seattle, USA): The largest year-round resort in the area offering more of everything for your vacation – at the best value! What can you enjoy while at the resort, aside from the mile-long sandy beaches of the lake? Check out our activities sure to excite both young and young-at-heart guests. We have it all, including being named “Property of the Year” and a “Top Ten Resort” by top publications.


Search results using vector: 
    6 (in San Francisco, USA): Newest kid on the downtown block. Steps away from the most popular destinations in downtown, enjoy free WiFi, an indoor rooftop pool & fitness center, 24 Grab'n'Go & drinks at the bar (score: 0.6350645)
    27 (in Aventura, USA): Complimentary Airport Shuttle & WiFi. Book Now and save - Spacious All Suite Hotel, Indoor Outdoor Pool, Fitness Center, Florida Green certified, Complimentary Coffee, HDTV (score: 0.62773544)
    25 (in Metairie, USA): Newly Redesigned Rooms & airport shuttle. Minutes from the airport, enjoy lakeside amenities, a resort-style pool & stylish new guestrooms with Internet TVs. (score: 0.6193533)


Search results using hybrid: 
    25 (in Metairie, USA): Newly Redesigned Rooms & airport shuttle. Minutes from the airport, enjoy lakeside amenities, a resort-style pool & stylish new guestrooms with Internet TVs. (score: 0.03279569745063782)
    27 (in Aventura, USA): Complimentary Airport Shuttle & WiFi. Book Now and save - Spacious All Suite Hotel, Indoor Outdoor Pool, Fitness Center, Florida Green certified, Complimentary Coffee, HDTV (score: 0.032786883413791656)
    36 (in Memphis, USA): Stunning Downtown Hotel with indoor Pool. Ideally located close to theatres, museums and the convention center. Indoor Pool and Sauna and fitness centre. Popular Bar & Restaurant (score: 0.0317460335791111)
```

### Advanced: Agent and Plugin Integration

For a more advanced example, see `2_use_as_a_plugin.py`, which demonstrates how to expose the hotel search as a plugin to a agent, this showcases how you can use the collection to create multiple search functions for different purposes and with some set filters and customized output. It then uses those in an Agent to help the user.

### Advanced: Use the Azure AI Search integrated embedding generation

For more info on this topic, see the [Azure AI Search documentation](https://learn.microsoft.com/en-us/azure/search/search-how-to-integrated-vectorization?tabs=prepare-data-storage%2Cprepare-model-aoai).

To use this, next to the steps needed to create the embedding skillset, you need to:

1. Adapt the `vectorizers` list and the profiles list in `custom_index` in `data_model.py`.
1. Remove the `embedding_generator` param from the collection in both scripts.  
    By removing this, we indicate that the embedding generation takes place in the service.

---

**Note:**  
You no longer need to manually configure the index or upload data via the Azure Portal. All setup is handled by the Python code.

If you encounter issues, ensure your Azure credentials and endpoints are correctly configured in your environment.

---
