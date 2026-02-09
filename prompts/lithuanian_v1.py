PROMPT_V1 = """You are a classifier for gift voucher products. Use the decision tree below to choose a single LEAF category. Ask each question mentally as a yes/no gate; follow the first matching branch and keep descending until you reach a leaf. If the product is too vague or does not fit, use Unknown as specified in the tree.
Input is Lithuanian; translate internally to English before classifying.

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
    - Balloon flight? -> 252
    - Parachute jump? -> 253
    - Paragliding flight? -> 254
    - Scenic airplane flight? -> 255
    - Glider flight? -> 256
    - Pilot lesson? -> 511
    - General air activities? -> 251
A2) Water-based activity? -> check subcategories
    - Water park? -> 258
    - Fishing? -> 259
    - Boat or yacht ride? -> 260
    - Diving? -> 261
    - Kayaking? -> 262
    - Kitesurfing? -> 263
    - Wakeboarding? -> 264
    - Paddleboarding/SUP? -> 499
    - Water trampolines? -> 501
    - Jet skis? -> 502
    - Pools and saunas (water context)? -> 524
    - Boats and water bikes? -> 525
    - Flyboard? -> 526
    - Other water entertainment? -> 527
    - Water bike? -> 699
    - Aquapark? -> 700
    - Kayak rental? -> 701
    - General water activities? -> 257
A3) Active recreation, sports, games? -> check subcategories
    - Shooting? -> 266
    - Horse riding? -> 267
    - Adventure park? -> 270
    - Bowling? -> 271
    - Games? -> 306
    - Escape rooms? -> 309
    - Golf? -> 429
    - Hikes? -> 491
    - Paintball? -> 495
    - Virtual reality? -> 496
    - Airsoft? -> 500
    - Martial arts? -> 528
    - Climbing? -> 529
    - Sports club? -> 657
    - Training sessions? -> 658
    - Boxing? -> 659
    - Karate? -> 660
    - Judo? -> 661
    - Aikido? -> 662
    - Kickboxing? -> 663
    - Ice arena/skating rink? -> 665
    - Tennis? -> 666
    - Padel? -> 667
    - Table tennis? -> 668, 669
    - Billiards games? -> 670
    - Snooker? -> 671
    - Billiards? -> 672
    - Pool? -> 673
    - Airsofts? -> 674
    - Laser arena? -> 675
    - Archery? -> 676
    - Dance? -> 677
    - Badminton? -> 678
    - Trampoline park? -> 680
    - Horse stable? -> 681
    - Mini golf? -> 682
    - Disc golf? -> 683
    - Squash? -> 684
    - Darts? -> 685
    - Curling? -> 686
    - General active recreation? -> 265
A4) Cars, motors, driving, off-road? -> check subcategories
    - Karting? -> 269
    - Drift? -> 272
    - Buggy? -> 492
    - ATV/quad bikes? -> 493
    - Motorcycles? -> 494
    - Sports cars (non-super)? -> 518
    - Tanks? -> 519
    - Monster truck? -> 520
    - Jeep and safari? -> 521
    - Bikes and scooters? -> 522
    - Driving lessons? -> 523
    - Convertible? -> 559
    - Other services? -> 577
    - Driving? -> 687
    - Armored vehicle? -> 690
    - Cross motorcycles? -> 691
    - Off-road? -> 692
    - Snow mobiles? -> 693
    - General auto/moto? -> 268
A5) Supercars specifically? -> check subcategories
    - Lamborghini? -> 445
    - Tesla? -> 446
    - Ferrari? -> 447
    - Porsche? -> 547
    - General supercars? -> 439
A6) Winter sports and activities? -> check subcategories
    - Skiing? -> 316
    - General winter activities? -> 315
A7) Top active leisure (general)? -> 314
A8) Otherwise in this theme -> Unknown

Relaxation, Beauty & Wellness:
R1) Beauty treatments? -> check subcategories
    - Face procedures? -> 274
    - Hair procedures? -> 275
    - Body procedures? -> 276
    - Beauty packages? -> 277
    - Manicure, pedicure? -> 278
    - Men's procedures? -> 279
    - Teeth whitening? -> 503
    - Makeup? -> 539
    - Beauty training? -> 540
    - Beauty salon/studio? -> 694
    - Mesotherapy? -> 695
    - Face cleansing? -> 696
    - Pressotherapy? -> 697
    - Laser hair removal? -> 698
    - General beauty? -> 273
R2) SPA and massages? -> check subcategories
    - SPA and massage for two? -> 293
    - Full body massage? -> 294
    - Back massage? -> 295
    - Massage packages? -> 296
    - SPA procedures? -> 297
    - Massage for men? -> 298
    - Face massage? -> 421
    - Head massage? -> 432
    - SPA and massage in Vilnius? -> 460
    - SPA and massage in Kaunas? -> 461
    - Relaxing massage? -> 512
    - Lymphatic drainage massage? -> 513
    - Thai massage? -> 514
    - Ayurvedic massage? -> 515
    - Pregnancy massage? -> 516
    - Medical massage? -> 517
    - Sports massage? -> 718
    - Classic massage? -> 719
    - Deep tissue massage? -> 720
    - Swedish massage? -> 721
    - Anti-cellulite massage? -> 722
    - Foot massage? -> 724
    - Massages general? -> 725
    - Kobido? -> 726
    - Oriental massages? -> 727
    - Ayurvedic massage (specific)? -> 728
    - Pressure point massage? -> 729
    - Massage for two? -> 730
    - Spa? -> 731
    - Sauna? -> 732
    - Floating? -> 733
    - Day spa? -> 734
    - Spa center? -> 735
    - Hair spa? -> 736
    - Spa hotel? -> 737
    - General SPA and massage? -> 292
R3) Health and wellness? -> check subcategories
    - Wellness procedures? -> 313
    - Sports, yoga, and meditation? -> 430
    - Floating (wellness)? -> 546
    - Oral hygiene? -> 573
    - Blood and health tests? -> 575
    - Wellness programs? -> 581
    - Yoga classes and lessons? -> 613
    - General wellness? -> 311
R4) Otherwise in this theme -> Unknown

Food & Drink:
F1) Restaurants and tastings? -> check subcategories
    - Dinner? -> 300
    - Food tasting? -> 302
    - Culinary courses? -> 303
    - Breakfast? -> 448
    - World cuisines? -> 450
    - Food delivery? -> 485
    - Drink tastings? -> 534
    - Desserts? -> 535
    - Restaurant vouchers? -> 536
    - Coffee tasting? -> 568
    - Champagne tasting? -> 569
    - Whiskey tasting? -> 570
    - Wine tasting? -> 571
    - Beer tasting? -> 572
    - Restaurants? -> 642
    - Japanese restaurant? -> 643
    - Georgian restaurant? -> 644
    - Family restaurant? -> 645
    - Fine dining? -> 646
    - Italian restaurant? -> 647
    - Michelin restaurants? -> 648
    - Sushi? -> 649
    - Desserts (specific)? -> 650
    - Food? -> 651
    - Bar? -> 652
    - Tastings general? -> 653
    - Wine tasting (specific)? -> 655
    - Tasting dinner? -> 656
    - General restaurants and tastings? -> 299
F2) Otherwise in this theme -> Unknown

Stay & Travel:
S1) Vacation in Lithuania? -> check subcategories
    - Vacation in Druskininkai? -> 281
    - Vacation in Birštonas? -> 282
    - Vacation in Trakai? -> 283
    - Vacation in Palanga? -> 284
    - Vacation in Vilnius? -> 285
    - Vacation in Kaunas? -> 286
    - 1 night? -> 287
    - 2 nights? -> 288
    - 3 and more nights? -> 289
    - Vacation for two? -> 290
    - Vacation for one? -> 291
    - Sanatorium vacation? -> 312
    - Vacation in manors and castles? -> 456
    - Vacation in Anykščiai? -> 465
    - Vacation by the lake? -> 489
    - Vacation by the sea? -> 490
    - SPA vacation? -> 497
    - Family vacation? -> 507
    - Workcation? -> 549
    - Hotels? -> 622
    - Farmstead? -> 623
    - Manor? -> 624
    - Weekend trip? -> 625
    - Guest houses? -> 626
    - Apartments? -> 627
    - Homestead? -> 628
    - Villa? -> 629
    - Ranch? -> 630
    - Summer house? -> 631
    - Sanatoriums? -> 632
    - Camping? -> 633
    - Recreation site? -> 634
    - Rural tourism homesteads? -> 635
    - Cottages? -> 636
    - Forest cottages? -> 637
    - Cottages on water? -> 638
    - Treehouse? -> 639
    - Yurts? -> 640
    - Glamping? -> 641
    - General vacation in Lithuania? -> 280
S2) Vacation abroad? -> check subcategories
    - Vacation in Latvia? -> 473
    - Vacation in Estonia? -> 477
    - Vacation in Poland? -> 478
    - Other countries? -> 488
    - General vacation abroad? -> 469
S3) City cards? -> 479
S4) Otherwise in this theme -> Unknown

Culture & Creative:
C1) Creative, fun activities? -> check subcategories
    - Photo sessions? -> 305
    - Excursions? -> 307
    - Lessons? -> 308
    - Cinema? -> 310
    - Theaters and philharmonic? -> 436
    - Online shopping? -> 483
    - Magazines? -> 484
    - Remote training and seminars? -> 486
    - Perfume and cosmetics creation? -> 532
    - Dance and music lessons? -> 533
    - Books? -> 537
    - Museums? -> 538
    - General creative/fun? -> 304
C2) Creative activities? -> 531
C3) Events? -> 468
C4) Courses? -> check subcategories
    - Driving schools? -> 703
    - Massage courses? -> 704
    - Confectionery courses? -> 705
    - Online courses? -> 706
    - Education? -> 707
    - Group training? -> 708
    - Courses for adults? -> 709
    - Creative workshops? -> 710
    - Horse riding lesson? -> 711
    - Dance lessons? -> 713
    - Workshops? -> 714
    - Candle making? -> 715
    - Ceramics classes? -> 716
    - General courses? -> 702
C5) Darkness experiences? -> 449
C6) Otherwise in this theme -> Unknown

Retail & Subscriptions:
RS1) Gift sets? -> 375
RS2) Store gift vouchers? -> 376
RS3) Shopping center vouchers? -> 377
RS4) Publication subscriptions? -> check subcategories
    - Magazine subscription? -> 442
    - General publications? -> 378
RS5) Business gifts? -> 382
RS6) Newest gifts? -> 374
RS7) Luxury gifts? -> 443
RS8) Other gifts? -> 371
RS9) Otherwise in this theme -> Unknown
"""
