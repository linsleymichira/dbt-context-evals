{% docs orders_status %}

Orders can be one of the following statuses:

| status code    | description                                                                                                            |
|----------------|------------------------------------------------------------------------------------------------------------------------|
| 10             | The order has been placed but has not yet left the warehouse                                                           |
| 20             | The order has ben shipped to the customer and is currently in transit                                                  |
| 30             | The order has been received by the customer                                                                            |
| 40             | The customer has indicated that they would like to return the order, but it has not yet been received at the warehouse |
| 50             | The order has been returned by the customer and received at the warehouse                                              |


{% enddocs %}
