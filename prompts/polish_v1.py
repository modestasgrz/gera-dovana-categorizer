PROMPT_V1 = """You are a classifier for gift voucher products. Use the decision tree below to choose a single LEAF category. Ask each question mentally as a yes/no gate; follow the first matching branch and keep descending until you reach a leaf. If the product is too vague or does not fit, use Unknown as specified in the tree.
Input is Polish; translate internally to English before classifying.

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
    - Paragliding flight? -> 356
    - Airplane flight? -> 358
    - Glider flight? -> 359
    - Helicopter flight? -> 360
    - Balloon flight? -> 361
    - Pilot course? -> 362
    - Scenic flight? -> 366
    - Motorglider flight? -> 736
    - Light aircraft flight? -> 975
    - Wind tunnel? -> 363
    - Parachute jump? -> 364
    - Dream jump? -> 365
    - Bungee jump? -> 532
    - Tandem jump? -> 1017
    - Motorparagliding flight? -> 1173
    - General flights category? -> 355
    - General jumps category? -> 531
    - Flights and jumps general? -> 1172
A2) Driving, cars, vehicles? -> check subcategories
    - Off-road? -> 369
    - Karting? -> 370
    - Motorcycles general? -> 371
        - Cross riding? -> 895
        - Scooter riding? -> 896
        - Motorcycle training? -> 897
        - Harley riding? -> 1040
    - Quads? -> 372
        - Buggy riding? -> 1037
    - Special vehicles? -> 374
        - Cucumber ride? -> 1042
        - Truck ride? -> 1043
    - Drifting? -> 543
    - Rally cars? -> 559
        - Mitsubishi ride? -> 904
        - Subaru ride? -> 908
    - Sports cars? -> 560
        - Ford ride? -> 898
        - Audi ride? -> 899
        - Nissan ride? -> 900
        - BMW ride? -> 902
        - Porsche ride? -> 903
        - Tesla ride? -> 907
        - Lamborghini passenger? -> 1151
        - Ferrari passenger? -> 1152
        - Porsche passenger? -> 1154
    - Supercars? -> 501
        - Car battles? -> 544
        - City driving? -> 618
        - Lamborghini driving? -> 685
        - Ferrari driving? -> 686
        - 4x4 driving? -> 687
        - Car rental? -> 894
        - Race car driving? -> 901
        - Race track driving? -> 1153
    - Military vehicles? -> 568
    - Track driving general? -> 814 (or specific tracks 871-892, 503-512, 547)
    - Fast cars? -> 816
    - Monster truck? -> 905
    - Tank driving? -> 906
        - Tank passenger? -> 1155
    - Motorcycle track? -> 1022
    - Buggy? -> 1148
    - Driving lessons? -> 1150
        - Safe driving training? -> 375
        - Car driving lessons? -> 815
        - Extreme driving course? -> 1157
    - Race track driving? -> 1156
    - General driving category? -> 367
A3) Water sports/activities? -> check subcategories
    - Flyboard? -> 377
    - Windsurfing? -> 378
    - Jet skis? -> 379
    - Diving? -> 380
    - Yachts? -> 381
    - Kayaking? -> 382
    - Aquapark? -> 383
    - Sailing? -> 384
    - Wakeboarding? -> 385
    - Rafting? -> 651
    - Kitesurfing? -> 689
    - Motorboat? -> 690
    - Ship cruise? -> 691
    - Sailing course? -> 692
    - Motorboat course? -> 693
    - SUP? -> 1183
    - General water sports? -> 376
A4) Shooting activities? -> check subcategories
    - Shooting range general? -> 401
        - Firearm shooting? -> 854
            - Rifle shooting? -> 855
            - Pistol shooting? -> 856
            - Historical weapons? -> 857
        - Shooting training? -> 858
        - Dynamic shooting? -> 859
        - Sport shooting? -> 860
        - Clay shooting? -> 864
    - Paintball? -> 402
    - Laser paintball? -> 403
    - Axe throwing? -> 694
    - Shooting for kids? -> 861
    - Shooting for two? -> 862
    - Archery? -> 863
    - General shooting? -> 400
A5) Extreme sports? -> 652
A6) Close to nature activities? -> check subcategories
    - Survival? -> 412
    - Animals? -> 727
    - Nature? -> 728
    - General nature category? -> 726
A7) Active leisure/recreation? -> check subcategories
    - Gym? -> 393
    - Horse riding? -> 408
    - Climbing? -> 409
    - Tennis? -> 411
    - Golf? -> 413
        - Minigolf? -> 1142
    - Winter sports? -> 615
    - Trampoline park? -> 730
    - Rope park? -> 731
    - Fitness? -> 732
    - Yoga? -> 733
    - Squash? -> 734
    - Zipline? -> 735
    - Martial arts? -> 1003
    - Amusement park? -> 1143
    - Climbing wall? -> 1144
    - Pole dance? -> 1145
    - VR glasses? -> 1146
    - General active leisure? -> 729
A8) Otherwise in this theme -> Unknown

Relaxation, Beauty & Wellness:
R1) Health and relaxation? -> check subcategories
    - SPA and wellness? -> 392
    - Salt cave? -> 394
    - Medical packages? -> 676
    - Oxygen therapy? -> 1005
    - General health/relax? -> 387
R2) Massages? -> check subcategories
    - Thai massage? -> 787
    - Chinese cupping? -> 788
    - Relaxing massage? -> 789
    - Lomi lomi massage? -> 790
    - Classic massage? -> 791
    - Hot stone massage? -> 792
    - Balinese massage? -> 793
    - Face massage? -> 794
    - Foot massage? -> 795
    - Back massage? -> 796
    - Ayurvedic massage? -> 797
    - Medical massage? -> 798
    - Oriental massage? -> 799
    - Sports massage? -> 800
    - Head massage? -> 801
    - Couples massage? -> 802
    - Chocolate massage? -> 803
    - Pregnancy massage? -> 804
    - Full body massage? -> 805
    - Stamp massage? -> 806
    - Honey massage? -> 807
    - Aromatherapy massage? -> 808
    - Candle massage? -> 809
    - Kobido massage? -> 1001
    - Lymphatic drainage? -> 1131
    - Reflexology? -> 1132
    - Deep tissue massage? -> 1134
    - Hot stones massage? -> 1135
    - Shiatsu massage? -> 1136
    - Anti-cellulite massage? -> 1137
    - Neck massage? -> 1138
    - Hand massage? -> 1139
    - Pregnancy massage? -> 1140
    - Herbal stamp massage? -> 1141
    - General massage category? -> 388
R3) Beauty treatments? -> check subcategories
    - Body treatments? -> 389
    - Face treatments? -> 390
    - Manicure? -> 391
    - Makeovers? -> 395
    - Makeup and styling? -> 715
    - Cosmetic treatments? -> 716
    - Pedicure? -> 717
    - Peeling? -> 1177
    - General beauty? -> 725
R4) SPA experiences? -> check subcategories
    - Floating? -> 659
    - Thermal baths? -> 688
    - Sauna? -> 1000
    - Spa resort? -> 1095
    - Hammam? -> 1096
    - Head SPA? -> 1097
    - SPA for couples? -> 1098
    - SPA hotel? -> 1099
        - SPA resort? -> 1100
    - Day SPA? -> 1101
    - SPA for women? -> 1102
    - SPA treatment? -> 1103
    - SPA for men? -> 1104
    - General SPA? -> 1094
R5) Hair styling? -> 1015
R6) Otherwise in this theme -> Unknown

Food & Drink:
F1) Restaurants and dining? -> check subcategories
    - Culinary workshops? -> 398
    - Romantic dinner? -> 593
    - Dessert? -> 594
    - Coffee and tea? -> 595
    - Barista course? -> 678
    - Bartender course? -> 679
    - Dinners for two? -> 718
    - Restaurant in the dark? -> 719
    - Restaurants general? -> 1118
        - Polish restaurant? -> 1119
        - Vegetarian restaurant? -> 1120
        - Italian restaurant? -> 1121
        - Fish restaurant? -> 1122
    - Sushi? -> 1123
    - Inn/tavern? -> 1124
    - Steakhouse? -> 1125
    - Winery? -> 1126
    - Tastings general? -> 1128
        - Wine tasting? -> 397
        - Whiskey tasting? -> 720
        - Beer tasting? -> 721
    - General restaurants/tastings? -> 396
F2) Culinary courses? -> 984
F3) Otherwise in this theme -> Unknown

Stay & Travel:
S1) Travel and accommodation? -> check subcategories
    - Mazury? -> 415
    - Mountains? -> 416
    - Sea? -> 417
    - City weekend? -> 418
    - SPA stay? -> 420
    - Sanatorium stay? -> 682
    - SPA weekend? -> 683
    - Weekend trips? -> 684
    - Abroad vacation general? -> 781
        - Lithuania vacation? -> 782
        - Other countries? -> 783
        - Italy? -> 1044
        - Hungary? -> 1045
        - Norway? -> 1046
    - Glamping? -> 944
    - Day trips? -> 976
    - Romantic weekend for two with jacuzzi? -> 1004
    - SPA stay with treatments? -> 1021
    - SPA weekend by the sea? -> 1023
    - Hotel? -> 1105
    - Castle? -> 1106
    - Sanatorium? -> 1107
    - Seaside accommodation? -> 1108
    - Manor? -> 1109
    - Treehouse? -> 1110
    - Mountain cottages? -> 1111
    - Weekend for two? -> 1112
    - Villa? -> 1113
    - Guest house? -> 1114
    - Resort? -> 1115
    - Holidays in Poland? -> 1117
    - General travel? -> 414
S2) Otherwise in this theme -> Unknown

Culture & Creative:
C1) Culture and entertainment? -> check subcategories
    - Theater? -> 399
    - Escape room? -> 527
    - Amusement parks? -> 578
    - Virtual reality? -> 605
    - Billiards? -> 680
    - Bowling? -> 681
    - Cinema? -> 722
    - Music workshops? -> 724
    - Museum? -> 999
    - Shopping with stylist? -> 1029
    - General culture/entertainment? -> 407
C2) Learning and fun? -> check subcategories
    - Photo session? -> 405
    - Photography course? -> 406
    - Dance lessons? -> 410
    - Creative workshops? -> 423
    - Pilot courses? -> 424
    - Skill courses? -> 427
    - Language courses? -> 723
    - Singing lessons? -> 1014
    - Drawing lessons? -> 1019
    - Instrument lessons? -> 1034
    - General learning/fun? -> 421
C3) Home attractions? -> check subcategories
    - Takeaway food? -> 751
    - Online courses/workshops? -> 752
    - General home attractions? -> 749
C4) Fun & Creative? -> check subcategories
    - Workshops general? -> 1159
        - Workshops for kids? -> 1160
        - Interesting workshops for adults? -> 1161
    - Training? -> 1162
        - Dog training? -> 1163
    - Courses? -> 1164
        - Makeup course? -> 1165
    - Photo session? -> 1169
    - Dance lesson? -> 1170
    - City game? -> 1171
    - General Fun&Creative? -> 1158
C5) Otherwise in this theme -> Unknown

Retail & Subscriptions:
RS1) Gift sets? -> 489
RS2) Exclusive gifts? -> 616
RS3) Store gift vouchers? -> 868
RS4) Shopping center gift cards? -> 950
RS5) City gift cards? -> 998
RS6) Otherwise in this theme -> Unknown
"""
