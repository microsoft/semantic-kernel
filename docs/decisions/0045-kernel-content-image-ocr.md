---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: rogerbarreto
date: 2024-05-02
deciders: rogerbarreto, markwallace-microsoft, sergeymenkshi, dmytrostruk, sergeymenshik, westey-m, matthewbolanos
---

# Kernel Content Image OCR

## Context and Problem Statement

Currently, we do have AI Models specialized on extracting valuable data from Images provide them in a structured way to the user. This is a common scenario for OCR (Optical Character Recognition) models and services.

Different services provide some level of similarity on the structure of the data extracted, but they can have different properties and metadata.

The proposed solution is to create a specialized `KernelContent` type for Image OCR results that can abstract the common properties and metadata from different services and provide a clear way to access the extracted data.

### Resources and References

- [Azure Computer Vision Image Analysis](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/concept-ocr#text-extraction-example)
- [Azure Computer Vision OCR](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/how-to/call-read-api)
- [Amazon Text Extractor](https://docs.aws.amazon.com/textract/latest/dg/API_GetDocumentTextDetection.html)
- [Google Document AI](https://cloud.google.com/static/document-ai/docs/images/invoice.json)
- [Hugging Face OCR](https://huggingface.co/models?pipeline_tag=ocr)

## Decision Drivers

- Simple approach, minimal complexity
- Allow extensibility
- Concise and clear

### Azure Computer Vision OCR

Reduced OCR Structure - [Full Sample Here](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/concept-ocr#text-extraction-example)

Image Analysis Result

```json
{
  "modelVersion": "2024-02-01",
  "metadata": {
    "width": 1000,
    "height": 945
  },
  "readResult": {
    "blocks": [
      {
        "lines": [
          {
            "text": "You must be the change you",
            "boundingPolygon": [
              { "x": 251, "y": 265 },
              { "x": 673, "y": 260 },
              { "x": 674, "y": 308 },
              { "x": 252, "y": 318 }
            ],
            "words": [
              {
                "text": "You",
                "boundingPolygon": [
                  { "x": 252, "y": 267 },
                  { "x": 307, "y": 265 },
                  { "x": 307, "y": 318 },
                  { "x": 253, "y": 318 }
                ],
                "confidence": 0.996
              },
              ...
            ]
          },
          ...
        ]
      }
    ]
  }
}
```

OCR Result:

```json
{
  "status": "succeeded",
  "createdDateTime": "2021-02-04T06:32:08.2752706+00:00",
  "lastUpdatedDateTime": "2021-02-04T06:32:08.7706172+00:00",
  "analyzeResult": {
    "version": "3.2",
    "readResults": [
      {
        "page": 1,
        "angle": 2.1243,
        "width": 502,
        "height": 252,
        "unit": "pixel",
        "lines": [
          {
            "boundingBox": [58, 42, 314, 59, 311, 123, 56, 121],
            "text": "Tabs vs",
            "appearance": {
              "style": {
                "name": "handwriting",
                "confidence": 0.96
              }
            },
            "words": [
              {
                "boundingBox": [68, 44, 225, 59, 224, 122, 66, 123],
                "text": "Tabs",
                "confidence": 0.933
              },
              {
                "boundingBox": [241, 61, 314, 72, 314, 123, 239, 122],
                "text": "vs",
                "confidence": 0.977
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Amazon Textract OCR

Reduced OCR Structure - [Full Sample Here](https://docs.aws.amazon.com/textract/latest/dg/sync-calling.html#sync-response)

```json
{
    {
        "DocumentMetadata": {
            "Pages": 1
        },
        "Blocks": [
            {
                "BlockType": "PAGE",
                "Geometry": {
                    "BoundingBox": {
                        "Width": 0.9995205998420715,
                        "Height": 1.0,
                        "Left": 0.0,
                        "Top": 0.0
                    },
                    "Polygon": [
                        {
                            "X": 0.0,
                            "Y": 0.0
                        },
                        ...
                    ]
                },
                "Id": "ca4b9171-7109-4adb-a811-e09bbe4834dd",
                "Relationships": [
                    {
                        "Type": "CHILD",
                        "Ids": [...]
                    }
                ]
            },
            {
                "BlockType": "LINE",
                "Confidence": 99.93761444091797,
                "Text": "Employment Application",
                "Geometry": {
                    "BoundingBox": {
                        "Width": 0.3391372561454773,
                        "Height": 0.06906412541866302,
                        "Left": 0.29548385739326477,
                        "Top": 0.027493247762322426
                    },
                    "Polygon": [
                        {
                            "X": 0.29548385739326477,
                            "Y": 0.027493247762322426
                        },
                        {
                            "X": 0.6346210837364197,
                            "Y": 0.027493247762322426
                        },
                        {
                            "X": 0.6346210837364197,
                            "Y": 0.0965573713183403
                        },
                        {
                            "X": 0.29548385739326477,
                            "Y": 0.0965573713183403
                        }
                    ]
                },
                "Id": "26085884-d005-4144-b4c2-4d83dc50739b",
                "Relationships": [
                    {
                        "Type": "CHILD",
                        "Ids": [
                            "ed48dacc-d089-498f-8e93-1cee1e5f39f3",
                            "ac7370f3-cbb7-4cd9-a8f9-bdcb2252caaf"
                        ]
                    }
                ]
            },
            {
                "BlockType": "WORD",
                "Confidence": 99.97914123535156,
                "Text": "current",
                "TextType": "HANDWRITING",
                "Geometry": {
                    "BoundingBox": {
                        "Width": 0.12791454792022705,
                        "Height": 0.04768490046262741,
                        "Left": 0.8387037515640259,
                        "Top": 0.8843405842781067
                    },
                    "Polygon": [
                        {
                            "X": 0.8387037515640259,
                            "Y": 0.8843405842781067
                        },
                        ...
                    ]
                },
                "Id": "549ef3f9-3a13-4b77-bc25-fb2e0996839a"
            }
        ],
        "DetectDocumentTextModelVersion": "1.0",
        "ResponseMetadata": {
            "RequestId": "337129e6-3af7-4014-842b-f6484e82cbf6",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "337129e6-3af7-4014-842b-f6484e82cbf6",
                "content-type": "application/x-amz-json-1.1",
                "content-length": "45675",
                "date": "Mon, 09 Nov 2020 23:54:38 GMT"
            },
            "RetryAttempts": 0
        }
    }
}
```

### Google Document AI OCR

Reduced OCR Structure - [Full Sample Here](https://cloud.google.com/static/document-ai/docs/images/invoice.json)

```json
{
    "uri": "",
    "mimeType": "image/png",
    "text": "Invoice\nDate: 2020/01/01\nInvoice no: 1001\nTO:\nFROM: Google Singapore",
    "pages": [
        {
            "pageNumber": 1,
            "dimension": {
                "width": 916,
                "height": 1052,
                "unit": "pixels"
            },
            "layout": {
                "textAnchor": {
                    "textSegments": [
                        {
                            "endIndex": "464"
                        }
                    ]
                },
                "boundingPoly": {
                    "vertices": [
                        {},
                        {
                            "x": 916
                        },
                        {
                            "x": 916,
                            "y": 1052
                        },
                        {
                            "y": 1052
                        }
                    ],
                    "normalizedVertices": [
                        {},
                        {
                            "x": 1
                        },
                        {
                            "x": 1,
                            "y": 1
                        },
                        {
                            "y": 1
                        }
                    ]
                },
                "orientation": "PAGE_UP"
            },
            "detectedLanguages": [
                {
                    "languageCode": "en"
                },
                {
                    "languageCode": "und"
                },
                {
                    "languageCode": "id"
                }
            ],
            "blocks": [...]
            "paragraphs": [...]
            "lines": [...]
        },
    ],
    "entities": [
        {
            "textAnchor": {
                "textSegments": [
                    {
                        "startIndex": "399",
                        "endIndex": "406"
                    }
                ]
            },
            "type": "vat",
            "mentionText": "$140.00",
            "confidence": 1,
            "pageAnchor": {
                "pageRefs": [
                    {
                        "boundingPoly": {
                            "normalizedVertices": [
                                {
                                    "x": 0.72598255,
                                    "y": 0.70342207
                                },
                                {
                                    "x": 0.7947598,
                                    "y": 0.70342207
                                },
                                {
                                    "x": 0.7947598,
                                    "y": 0.7214829
                                },
                                {
                                    "x": 0.72598255,
                                    "y": 0.7214829
                                }
                            ]
                        }
                    }
                ]
            },
            "id": "0",
            "properties": [
                {
                    "textAnchor": {
                        "textSegments": [
                            {
                                "startIndex": "399",
                                "endIndex": "406"
                            }
                        ],
                        "content": "$140.00"
                    },
                    "type": "vat/tax_amount",
                    "mentionText": "$140.00",
                    "confidence": 0.0062551796,
                    "pageAnchor": {
                        "pageRefs": [
                            {
                                "boundingPoly": {
                                    "normalizedVertices": [
                                        {
                                            "x": 0.72598255,
                                            "y": 0.70342207
                                        },
                                        {
                                            "x": 0.7947598,
                                            "y": 0.70342207
                                        },
                                        {
                                            "x": 0.7947598,
                                            "y": 0.7214829
                                        },
                                        {
                                            "x": 0.72598255,
                                            "y": 0.7214829
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                    "id": "1",
                    "normalizedValue": {
                        "text": "140 USD",
                        "moneyValue": {
                            "currencyCode": "USD",
                            "units": "140"
                        }
                    }
                }
            ]
        },
        ...
    ]
}
```

### Hugging Face - Image to Text OCR

Looking at the Image-To-Text models from Hugging Face, I couldn't find a clear structure for the OCR results.

The models have different ways of dealing with the images, most of them return in the Text Generation format in a single string.

Most Capable OCR model identified was **jinhybr/OCR-Donut-CORD** which still doesn't work very well and ouptuts incomplete or broken structures

OCR Structure Model **jinhybr/OCR-Donut-CORD**

Sample 1 - Plain Text as XML

Provided American Express Website Error Message, the OCR output was low quality and incomplete

```
<s_cord-v2>
   <s_menu>
       <s_nm>My Account Candys</s_nm>
       <s_unitprice>Insurance</s_unitprice>
       <s_cnt>Q</s_cnt>
       <s_price>Contact Us</s_nm>
       <s_price>Login</s_price>
       <s_sub>
           <s_nm>We're Sorry</s_nm>
           <sep/>
           <s_nm>You are not authorized toga into this application athis time. Pleasereachoutto your program</s_nm>
           <s_price>administrator foram</s_nm>
           <s_price>additional</s_price>
           <s_sub>
               <s_nm>information.</s_nm>
           </s_sub>
           <sep/>
           <s_nm>We'vere unabletoprocess your request.</s_nm>
       </s_sub>
       <sep/>
       <s_nm>Encor Coche: ac235-ゆ13e-lacT.B91Q-02Blasfbbee</s_nm>
   </s_sub>
</s_menu>
<s_sub_total>
   <s_subtotal_price>tor additional</s_subtotal_price>
   <s_discount_price>
```

Sample 2 - Plain Text as XML

```
<s_cord-v2>
   <s_menu>
       <s_nm>RATE Services</s_nm>
       <s_price>Smooth</s_price>
       <sep/>
       <s_nm>RATE Services</s_nm>
       <s_price>- Dynamisant</s_nm>
       <s_price>---</s_price>
       <sep/>
       <s_nm>Thank you</s_nm>
       <s_price>---</s_price>
       <sep/>
       <s_nm>Youreference numberis Discover</s_nm>
       <s_price>---</s_price>
       <sep/>
       <s_nm>All your requests have been successfully submitted.</s_nm>
       <s_price>---</s_price>
       <sep/>
       <s_nm>SHRKEKO GARING IS</s_nm>
       <s_price>---</s_price>
       <sep/>
       <s_nm>
```

Sample 3 - Plain Text as XML

Provided a Hospital Receipt and the OCR output was incorrect, invalid XML and incomplete

```
<s_cord-v2>
   <s_menu>
       <s_nm>Hospitel</s_nm>
       <s_unitprice>@014</s_unitprice>
       <s_cnt>4</s_cnt>
       <s_price>4834</s_subtotal_price>
       <s_discount_price>313</s_discount_price>
   </s_sub_total>
   <s_total>
       <s_total_price>4834
           <sep/>
           <s_nm>Smoking Sales</s_nm>
           <s_unitprice>@014</s_unitprice>
           <s_cnt>4</s_cnt>
           <s_price>4834</s_price>
           <sep/>
           <s_nm>EUK</s_nm>
           <s_unitprice>20,000</s_unitprice>
           <s_cnt>3</s_cnt>
           <s_price>SUSHIKO</s_nm>
           <s_unitprice>BOX</s_nm>
           <s_unitprice>@014</s_unitprice>
           <s_cnt>3</s_cnt>
           <s_price>SUSHIKO SUSHIKO SUSHIKO SUSHIKO SUSHIKO SUSHIKO SUSHIKO SUSHIKO SUSHIKO SUSHIKO SUSHIKO ...
```

## Initial Considerations

Currently we don't have a very capable AI Model that is strictly dedicated to output OCR results in a structured way.

The best model identified in Hugging Face was **jinhybr/OCR-Donut-CORD**, but it still doesn't work very well

- Incomplete outputs
- Allucinates the OCR structure
- Outputs invalid XML

It's not very clear if worth adding this abstraction to use with OCR Services and not against AI Models directly (Primary Goal of SK)

## Kernel Contents for OCR

Potential Names:

- `OCRJsonContent`
- `OCRContent`
- `ImageOCRContent`

### Option 1 - JsonContent

Instead of creating a full abstraction for OCR we can provide a `JsonContent` abstraction that will allow multiple different representations of OCR results.

```csharp
public class JsonContent : KernelContent
{
    // Traversable JSON structure
    public JsonElement Content { get; set; }
}
```

Pros:

- Simple and flexible
- Can be used for other JSON structures not limited to OCR
- Is traversable and don't need to be deserialized
- Is not a breaking glass approach and will be clearly visible to the user

Cons:

- Not an abstraction dedicated for OCR results
- Users would need to implement different logic to handle different OCR service results

### Option 2 - OCRContent

Create a specialized `OCRContent` type that can abstract the common properties and metadata from different services and expose the underlying OCR Content as InnerContent, for breaking glass scenarios.

```csharp
public class OCRContent : KernelContent {
    public int Width { get; set; }
    public int Height { get; set; }
    public int Pages { get; set; }
    public string GeomeryUnit { get; set; }

    class Block {
        public string Type { get; set; }
        public string Text { get; set; }
        public double Confidence { get; set; } // 0.0-1.0
        public Geomery Geomery { get; set; }
    }

    class Geomery {
        public double Width { get; set; }
        public double Height { get; set; }
        public double Left { get; set; }
        public double Top { get; set; }

        public List<PointF> Polygon { get; set; }
    }
}
```

Pros:

- Abstracts a high level view of the OCR results
- Users can access the OCR results in a structured way
- For more complex scenarios, users can BreakGlass and access the InnerContent

### OCRContent Serialization Results for Azure, Amazon and Google

#### Azure Computer Vision OCRContent Serialization

Azure AI - Image Analysis:

```json
{
    "width": 1000,
    "height": 945,
    "pages": 1,
    "geomeryUnit": "pixel",
    "blocks": [
        {
            "type": "line",
            "text": "You must be the change you",
            "confidence": 0.996,
            "geometry": {
                "polygon": [
                    { "x": 251, "y": 265 },
                    { "x": 673, "y": 260 },
                    { "x": 674, "y": 308 },
                    { "x": 252, "y": 318 }
                ]
            }

        },
        {
            "type": "word",
            "text": "You",
            "confidence": 0.996,
            "geometry": {
                "polygon": [
                    { "x": 252, "y": 267 },
                    { "x": 307, "y": 265 },
                    { "x": 307, "y": 318 },
                    { "x": 253, "y": 318 }
                ]
            }
        },
        ...
    ]
}
```

Azure AI - OCR Analysis:

```json
{
    "width": 1000,
    "height": 945,
    "pages": 1,
    "geomeryUnit": "pixel",
    "blocks": [
        {
            "type": "line",
            "text": "Tabs vs",
            "confidence": 0.96,
            "geometry": {
                "polygon": [
                    { "x": 58, "y": 42 },
                    { "x": 314, "y": 59 },
                    { "x": 311, "y": 123 },
                    { "x": 56, "y": 121 }
                ]
            }
        },
        {
            "type": "word",
            "text": "Tabs",
            "confidence": 0.933,
            "geometry": {
                "polygon": [
                    { "x": 68, "y": 44 },
                    { "x": 225, "y": 59 },
                    { "x": 224, "y": 122 },
                    { "x": 66, "y": 123 }
                ]
            }
        },
        ...
    ]
}
```

#### Amazon Textract OCRContent Serialization

Amazon Textract OCR

```json

{
    "width": 0.9995205998420715,
    "height": 1.0,
    "pages": 1,
    "geomeryUnit": "ratio",
    "blocks": [
        {
            "type": "line",
            "text": "Employment Application",
            "confidence": 99.93761444091797,
            "geometry": {
                "polygon": [
                    { "x": 0.29548385739326477, "y": 0.027493247762322426 },
                    { "x": 0.6346210837364197, "y": 0.027493247762322426 },
                    { "x": 0.6346210837364197, "y": 0.0965573713183403 },
                    { "x": 0.29548385739326477, "y": 0.0965573713183403 }
                ]
            }
        },
        {
            "type": "word",
            "text": "current",
            "confidence": 99.97914123535156,
            "geometry": {
                "polygon": [
                    {
                        "x": 0.8387037515640259,
                        "y": 0.8843405842781067
                    },
                    ...
                ]
            }
        },
        ...
    ],
    "metadata": { // From the KernelContent Metadata Property
        "RequestId": "337129e6-3af7-4014-842b-f6484e82cbf6",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "x-amzn-requestid": "337129e6-3af7-4014-842b-f6484e82cbf6",
            "content-type": "application/x-amz-json-1.1",
            "content-length": "45675",
            "date": "Mon, 09 Nov 2020 23:54:38 GMT"
        },
        "RetryAttempts": 0
    }
}
```

#### Google Document AI OCRContent Serialization

Google Document AI

```json
{
    "width": 916,
    "height": 1052,
    "pages": 1,
    "geomeryUnit": "pixels",
    "blocks": [
        {
            "type": "entity",
            "text": "$140.00",
            "confidence": 1.0,
            "geometry": {
                "polygon": [
                    { "x": 0.72598255, "y": 0.70342207 },
                    { "x": 0.7947598, "y": 0.70342207 },
                    { "x": 0.7947598, "y": 0.7214829 },
                    { "x": 0.72598255, "y": 0.7214829 }
                ]
            },
            ...
        },
        ...
    ],
    "metadata": { // From the KernelContent Metadata Property
        "uri": "",
        "mimeType": "image/png",
        "text": "Invoice\nDate: 2020/01/01\nInvoice no: 1001\nTO:\nFROM: Google Singapore"
    }
}
```

### Decision Outcome

TBD
