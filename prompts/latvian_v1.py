PROMPT_V1 = """You are a classifier for gift voucher products. Use the decision tree below to choose a single LEAF category. Ask each question mentally as a yes/no gate; follow the first matching branch and keep descending until you reach a leaf. If the product is too vague or does not fit, use Unknown as specified in the tree.
Input is Latvian; translate internally to English before classifying.

Product entry:
- Name: {{PRODUCT_NAME}}
- Description: {{PRODUCT_DESCRIPTION}}
- Location: {{PRODUCT_LOCATION}}

OUTPUT:
Return ONLY a JSON object with keys: category, comment.
- category: leaf ID number from the tree, or Unknown.
- comment: one sentence.
If category != "Unknown":
"Chosen {category} (0.xx); considered {alt_category} (0.yy) but {short refusal reason}."
If category == "Unknown":
"Unknown (0.xx); considered {alt_category} (0.yy) but {one-sentence justification}."
Use numeric confidence scores between 0.00 and 1.00 with two decimals.

Top level:
1) Adventure, adrenaline, active leisure, sports, vehicles, outdoors? -> Adventure & Active
2) Relaxation, wellness, beauty, cosmetics, SPA, health/medical? -> Relaxation, Beauty & Wellness
3) Food, drink, dining, tasting, culinary? -> Food & Drink
4) Travel, stays, accommodation? -> Stay & Travel
5) Culture, creative, learning, arts, events, entertainment? -> Culture & Creative
6) Retail, gift sets, vouchers for goods, subscriptions? -> Retail & Subscriptions
7) Otherwise -> Unknown

Adventure & Active:
A1) Air-based activity (flights, jumps)? -> check subcategories
    - Balloon flight? -> 203
        - Balloon flight in Jelgava? -> 684
    - Parachute jump? -> 204
    - Paragliding flight? -> 205
    - Airplane flight? -> 206
    - Hang gliding flight? -> 207
    - Helicopter flight? -> 431
    - Bungee jump? -> 543
    - Flight over Riga? -> 685
        - Flight over Sigulda? -> 686
    - Motorized hang glider flight? -> 687
    - Wind tunnel (Aerodium)? -> 208
    - General flights and jumps? -> 202
A2) Water activities? -> check subcategories
    - Water park? -> 210
    - Yacht ride? -> 211
        - Yacht rental? -> 596
        - Motor yacht? -> 597
    - Diving? -> 212
    - Boat rental? -> 213
        - Kayak rental? -> 456
        - Canoe rental? -> 592
        - Motorboat? -> 593
        - Rowing boats? -> 594
    - Kiteboard? -> 214
    - Wakeboard? -> 215
    - Windsurfing? -> 216
    - Other water entertainment? -> 217
    - Fishing? -> 454
        - Fishing with accommodation? -> 595
    - Cruise? -> 457
    - SUP rental? -> 458
    - Boat ride? -> 459
    - Jet ski rental? -> 460
    - Rafts? -> 598
    - Water formula? -> 599
    - Efoil? -> 600
    - General water adventures? -> 209
A3) Active recreation? -> check subcategories
    - Shooting? -> 219
        - Shooting range? -> 466
        - Laser tag? -> 467
        - Archery? -> 468
        - Airsoft? -> 538
    - Horse riding? -> 220
    - Adventure parks? -> 223
    - Bowling? -> 224
    - Sports? -> 469
    - Bouldering? -> 470
    - VR? -> 471
    - Games? -> 472
    - Paintball? -> 542
    - Golf? -> 650
        - Classic golf? -> 651
        - Disc golf? -> 652
        - Mini golf? -> 653
        - Football golf? -> 654
    - Squash? -> 655
    - Entertainment? -> 656
    - Sports clubs? -> 658
    - Yoga? -> 659
    - Orienteering? -> 660
    - Hiking? -> 661
    - Curling? -> 662
    - Kickboxing? -> 663
    - Padel tennis? -> 682
    - Billiards? -> 771
    - General active recreation? -> 218
A4) Driving activities? -> check subcategories
    - Karting? -> 377
    - Supercar? -> 379
        - Ferrari ride? -> 473
        - Lamborghini ride? -> 474
    - Drift? -> 475
    - Quad bike ride? -> 476
    - Motorcycle ride? -> 477
    - Buggy ride? -> 478
    - Driving training? -> 479
    - Lamborghini (standalone)? -> 365
    - General driving? -> 221
A5) Winter activities? -> check subcategories
    - Skiing? -> 270
    - Snowboarding? -> 271
    - Snowmobile rides? -> 272
    - Ice skating? -> 273
    - Sleigh ride? -> 274
    - Bobsled track? -> 429
    - General winter activities? -> 269
A6) Outdoor entertainment? -> 420
A7) Otherwise in this theme -> Unknown

Relaxation, Beauty & Wellness:
R1) Beauty treatments? -> check subcategories
    - Face procedures? -> 226
    - Hair procedures? -> 227
    - Body procedures? -> 228
    - Treatment packages? -> 229
    - Manicure? -> 230
        - Japanese manicure? -> 716
        - French manicure? -> 717
        - Classic manicure? -> 718
    - Men's procedures? -> 231
    - Pedicure? -> 498
        - Medical pedicure? -> 719
        - Pedicure in Riga? -> 720
    - Waxing? -> 499
        - Waxing in Riga? -> 721
        - Bikini waxing? -> 722
        - Waxing for men? -> 723
            - Back waxing for men? -> 724
        - Face waxing? -> 725
    - Eyelashes and eyebrows? -> 500
        - Eyelash extensions? -> 726
        - Eyelash lamination? -> 727
        - Eyebrow lamination? -> 728
        - Permanent eyebrows? -> 729
        - Eyebrow correction? -> 730
        - Eyebrow coloring? -> 731
    - Barbershop? -> 501
    - Tattoo salon? -> 505
    - Nose and belly piercing? -> 506
    - Hairdresser? -> 712
    - Ear piercing? -> 713
        - Ear piercing in Riga? -> 714
        - Ear piercing for children? -> 715
    - Therapies? -> 732
        - Mesotherapy? -> 733
        - Cryotherapy? -> 734
        - Ultrasound therapy? -> 735
        - Endosphere therapy? -> 736
        - Physiotherapy? -> 744
        - Aromatherapy? -> 767
    - Laser hair removal? -> 737
    - Anti-ageing? -> 738
    - Lifting? -> 739
    - Dermapen? -> 740
    - Cavitation? -> 741
    - General beauty? -> 225
R2) SPA and massages? -> check subcategories
    - SPA and massage for two? -> 247
    - Back massage? -> 249
    - Massage for men? -> 252
    - Medical massage? -> 442
    - Lymphatic drainage massage? -> 446
    - LPG massage? -> 447
    - Relaxing massage? -> 449
    - Face massage? -> 450
    - Thai massage? -> 453
    - Massages general? -> 560
        - Full body massage? -> 248
        - Ayurvedic massage? -> 441
        - Head massage? -> 443
        - Pregnancy massage? -> 444
        - Hot stone massage? -> 445
        - Foot massage? -> 448
        - Chocolate massage? -> 451
        - Sports massage? -> 452
        - Vacuum massage? -> 565
        - Tactile massage? -> 566
    - SPA general? -> 561
        - SPA procedures? -> 251
        - Day SPA? -> 440
        - SPA gift cards? -> 555
    - SPA hotels in Latvia? -> 563
        - SPA manors? -> 564
    - Underwater massage? -> 568
    - SPA in Palanga? -> 760
    - SPA in Druskininkai? -> 765
    - General SPA and massages? -> 246
R3) Health and wellbeing? -> check subcategories
    - SPA centers? -> 265
    - Swimming pools? -> 266
        - Pools in Riga? -> 644
        - Pools in Jurmala? -> 645
    - Cryosauna? -> 267
    - Solarium? -> 268
    - Floating? -> 461
    - Salt room? -> 462
    - Sauna (pirts)? -> 463
        - Sauna in Riga? -> 635
        - Sauna in Pieriga? -> 636
        - Wooden sauna? -> 637
        - Small saunas? -> 638
        - Sauna houses? -> 639
        - Sauna with hot tub? -> 640
    - Hammam? -> 464
    - DNA test? -> 465
    - Dentistry? -> 502
        - Teeth whitening? -> 503
        - Dental hygiene? -> 504
    - Sauna ritual? -> 529
        - Sauna ritual for two? -> 641
        - Sauna ritual with sauna master? -> 642
        - Sauna SPA? -> 643
    - Pilates? -> 780
    - General health and wellbeing? -> 264
R4) Otherwise in this theme -> Unknown

Food & Drink:
F1) For gourmets? -> check subcategories
    - Dinner? -> 254
        - Romantic dinner? -> 507
        - Dinner in the dark? -> 536
        - Dinner in restaurant? -> 675
        - Family-friendly dinner? -> 676
        - Where to have dinner in Riga? -> 677
    - Tastings? -> 255
        - Wine tasting? -> 509
        - Beer tasting? -> 510
        - Vodka tasting? -> 679
    - Late breakfast? -> 362
    - Restaurants and cafes? -> 508
    - Dessert? -> 511
    - Food delivery? -> 515
    - Restaurants? -> 665
        - Italian restaurant? -> 666
        - Armenian restaurant? -> 667
        - Pizzeria? -> 680
        - Best restaurants? -> 681
    - Cafes? -> 668
        - Cafes in Old Riga? -> 669
        - Cafe in Riga center? -> 670
        - Cozy cafes? -> 671
        - Best cafes in Riga? -> 672
    - Breakfast? -> 673
    - Asian cuisine? -> 770
    - General gourmets category? -> 253
F2) Otherwise in this theme -> Unknown

Stay & Travel:
S1) Location-specific (mostly filters, use general categories)? -> check subcategories
    - Various cities/regions in Latvia: 174-198, 353-356, 364-393, 408, 548, 709
S2) Vacation in Latvia? -> check subcategories
    - Riga? -> 234
    - Kurzeme? -> 235
    - Zemgale? -> 236
    - Vidzeme? -> 237
    - Latgale? -> 238
    - 1 night? -> 240
    - 2 nights? -> 241
    - For 1 person? -> 242
    - Vacation for two? -> 243
    - For 3 people? -> 244
    - Family vacation? -> 245
    - Jurmala? -> 432
    - Sigulda? -> 433
    - SPA vacation? -> 434
        - SPA vacation in Riga? -> 583
        - SPA vacation in Jurmala? -> 584
        - SPA vacation in Latvia? -> 585
        - SPA vacation in Lithuania? -> 586
        - SPA vacation in Estonia? -> 587
    - Vacation by the sea? -> 435
    - Vacation cottages? -> 438
        - Cottages by the lake? -> 581
        - Cottages by the sea? -> 582
    - Vacation complex? -> 439
    - Romantic vacation for two? -> 525
    - Vacation places? -> 574
        - Vacation by the lake? -> 436
        - Vacation in countryside? -> 437
        - Vacation in nature? -> 532
    - Accommodations? -> 575
        - Accommodations by the sea? -> 576
        - Accommodations by the lake? -> 577
        - Beautiful accommodations in Latvia? -> 578
        - Romantic accommodations? -> 579
    - Sanatorium? -> 580
    - Vacation with children? -> 588
    - Vacation outside Riga? -> 589
    - Glamping? -> 757
    - Castle? -> 781
    - General vacation in Latvia? -> 233
S3) Vacation abroad? -> check subcategories
    - Lithuania? -> 239
        - Palanga? -> 374
        - Druskininkai? -> 378
        - Birstonas? -> 385
        - Sanatoriums in Lithuania? -> 520
        - Vilnius? -> 521
        - Siauliai? -> 522
        - Trakai? -> 523
        - SPA in Lithuania? -> 540
        - Klaipeda? -> 759
    - Estonia? -> 375
        - Vacation in Tallinn? -> 516
        - Vacation in Tartu? -> 517
        - SPA in Parnava? -> 518
        - Vacation in Saaremaa? -> 519
        - SPA in Estonia? -> 539
    - Poland? -> 414
    - General vacation abroad? -> 426
S4) City cards? -> 428
S5) Otherwise in this theme -> Unknown

Culture & Creative:
C1) Fun gifts/activities? -> check subcategories
    - Photo session? -> 258
        - Individual photo session? -> 480
        - Couple photo session? -> 481
        - Pregnancy photo session? -> 482
        - Christmas photo session? -> 483
        - Family photo session? -> 537
    - Excursions? -> 259
    - Quests? -> 260
    - Cinema? -> 261
    - Press subscriptions? -> 332
        - Men's magazines? -> 631
        - Children's magazines? -> 632
        - Youth magazines? -> 633
        - Crosswords? -> 634
    - Caricatures? -> 484
    - Zoo? -> 495
    - Theaters? -> 496
    - Interesting gifts? -> 497
    - General fun gifts? -> 257
C2) Courses and masterclasses? -> check subcategories
    - Dance classes? -> 222
    - Makeup and style courses? -> 232
    - Courses general? -> 256
        - Auto courses? -> 617
        - Massage courses? -> 756
    - Floristry courses? -> 485
    - Soap making? -> 486
    - Photo courses? -> 488
    - Painting courses? -> 489
    - Online courses? -> 490
    - Jewelry making? -> 491
    - Perfume workshop? -> 492
    - Music lessons? -> 493
    - Masterclasses? -> 612
        - Masterclasses for children? -> 613
        - Masterclasses for women? -> 614
        - Masterclasses for men? -> 615
    - Courses for adults? -> 618
    - Ceramics masterclass? -> 619
    - Cooking masterclasses? -> 620
        - Macaron masterclass? -> 621
        - Cake baking masterclass? -> 622
        - Pizza masterclass? -> 623
    - Drawing courses? -> 624
    - Perfume masterclass? -> 766
    - Candle making masterclass? -> 768
    - General courses and masterclasses? -> 263
C3) Entertainment from home? -> check subcategories
    - Books and magazines? -> 421
    - Takeaway food? -> 422
    - Online shopping? -> 423
    - Online seminars and training? -> 424
    - General home entertainment? -> 419
C4) Otherwise in this theme -> Unknown

Retail & Subscriptions:
RS1) Gift sets? -> 330
RS2) Store gift cards? -> 331
RS3) Shopping center gift cards? -> 404
RS4) Gift cards general? -> 554
    - Restaurant gift cards? -> 556
    - Experience gift cards? -> 557
    - Store gift cards? -> 558
    - Hotel gift cards? -> 559
    - Jewelry? -> 782
RS5) Otherwise in this theme -> Unknown
"""
