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
4) Travel, stays, accommodation, city passes? -> Stay & Travel
5) Culture, creative, learning, arts, events, venues? -> Culture & Creative
6) Retail, subscriptions, vouchers for goods, gift sets, charity gifts? -> Retail & Subscriptions
7) Otherwise -> Unknown

Adventure & Active:
A1) Air-based activity? -> 251
    - Balloon flight? -> 252
    - Parachute jump? -> 253
    - Paragliding? -> 254
    - Scenic airplane flight? -> 255
    - Glider flight? -> 256
    - Pilot lesson? -> 511
    - Other air-based -> 251
A2) Water-based activity? -> 257
    - Water park? -> 258
    - Fishing? -> 259
    - Boat or yacht ride? -> 260
    - Diving? -> 261
    - Kayaking/canoeing? -> 262
    - Kitesurfing? -> 263
    - Wakeboarding? -> 264
    - Paddleboarding? -> 499
    - Water trampolines? -> 501
    - Jet skis? -> 502
    - Pools/saunas by water? -> 524
    - Boats/water bikes? -> 525
    - Flyboard? -> 526
    - Other water-based -> 257
A3) Active leisure, games, climbing, quests? -> 265
    - Shooting? -> 266
    - Horse riding? -> 267
    - Adventure park? -> 270
    - Bowling? -> 271
    - Games? -> 306
    - Escape/logic rooms? -> 309
    - Golf? -> 429
    - Hikes? -> 491
    - Paintball? -> 495
    - VR? -> 496
    - Airsoft? -> 500
    - Martial arts? -> 528
    - Climbing? -> 529
    - Other active leisure -> 265
A4) Cars, motors, driving, off-road? -> 268
    - Karting? -> 269
    - Drift? -> 272
    - Buggy? -> 492
    - ATV/quad? -> 493
    - Motorcycles? -> 494
    - Sports cars (non-super)? -> 518
    - Tanks? -> 519
    - Monster truck? -> 520
    - Jeep/safari? -> 521
    - Bikes/scooters? -> 522
    - Driving lessons? -> 523
    - Convertible ride? -> 559
    - Other auto/moto -> 268
A5) Supercars specifically? -> 439
    - Lamborghini? -> 445
    - Tesla? -> 446
    - Ferrari? -> 447
    - Porsche? -> 547
    - Other supercar -> 439
A6) Winter sports/snow? -> 315
    - Skiing? -> 316
    - Other winter -> 315
A7) Otherwise in this theme -> Unknown

Relaxation, Beauty & Wellness:
R1) SPA or massages? -> 292
    - Couples SPA/massage? -> 293
    - Full-body massage? -> 294
    - Back massage? -> 295
    - Massage package? -> 296
    - SPA procedures? -> 297
    - Massage for men? -> 298
    - Face massage? -> 421
    - Head massage? -> 432
    - SPA/massage in Vilnius? -> 460
    - SPA/massage in Kaunas? -> 461
    - Relaxing massage? -> 512
    - Lymph drainage? -> 513
    - Thai massage? -> 514
    - Ayurvedic massage? -> 515
    - Pregnancy massage? -> 516
    - лечебни/medical massage? -> 517
    - Other SPA/massage -> 292
R2) Beauty treatments/cosmetics? -> 273
    - Face treatment? -> 274
    - Hair treatment? -> 275
    - Body treatment? -> 276
    - Beauty комплекс? -> 277
    - Manicure/pedicure? -> 278
    - Men-only procedures? -> 279
    - Teeth whitening? -> 503
    - Makeup? -> 539
    - Beauty training? -> 540
    - Other beauty -> 273
R3) Wellness/health routines or procedures? -> 311
    - Yoga classes? -> 613
    - Wellness procedures? -> 313
    - Sport/yoga/meditation? -> 430
    - Floating? -> 546
    - Oral hygiene? -> 573
    - Blood/health tests? -> 575
    - Wellness programs? -> 581
    - Other wellness -> 311
R4) Otherwise in this theme -> Unknown

Food & Drink:
F1) Dining/tastings/culinary? -> 299
    - Dinner? -> 300
    - Food tasting? -> 302
    - Cooking class? -> 303
    - Breakfast? -> 448
    - World cuisines? -> 450
    - Food delivery? -> 485
    - Drink tasting? -> 534
    - Desserts? -> 535
    - Restaurant vouchers? -> 536
    - Coffee tasting? -> 568
    - Champagne tasting? -> 569
    - Whiskey tasting? -> 570
    - Wine tasting? -> 571
    - Beer tasting? -> 572
    - Other dining/tasting -> 299
F2) Otherwise in this theme -> Unknown

Stay & Travel:
S1) Accommodation/stays? -> 280
    - Manor/castle stay? -> 456
    - Stay in Anykščiai? -> 465
    - Stay by a lake? -> 489
    - Stay by the sea? -> 490
    - SPA stay? -> 497
    - Family stay? -> 507
    - Workcation? -> 549
    - Sanatorium stay? -> 312
    - Stay in Druskininkai? -> 281
    - Stay in Birštonas? -> 282
    - Stay in Trakai? -> 283
    - Stay in Palanga? -> 284
    - Stay in Vilnius? -> 285
    - Stay in Kaunas? -> 286
    - 1 night? -> 287
    - 2 nights? -> 288
    - 3+ nights? -> 289
    - Stay for two? -> 290
    - Stay for one? -> 291
    - Other stay -> 280
S2) Abroad gifts/experiences? -> 249
    - Latvia experiences? -> 476
    - Other abroad gifts -> 249
S3) Abroad stays/relaxation? -> 469
    - Stay in Latvia? -> 473
    - Stay in Estonia? -> 477
    - Stay in Poland? -> 478
    - Other countries? -> 488
    - Other abroad stays -> 469
S4) City pass/card? -> 479
    - City card (any)? -> 479
S5) Otherwise in this theme -> Unknown

Culture & Creative:
C1) Creative/fun gifts, media, venues, classes? -> 304
    - Photoshoot? -> 305
    - экскурсия? -> 307
    - Lesson/class? -> 308
    - Cinema? -> 310
    - Theater/phil? -> 436
    - Online shopping voucher? -> 483
    - Magazines? -> 484
    - Remote training/seminars? -> 486
    - Perfume/cosmetics creation? -> 532
    - Dance/music lessons? -> 533
    - Books? -> 537
    - Museums? -> 538
    - Other creative/fun -> 304
C2) Hands-on creative activities/workshops? -> 531
    - Other creative activities -> 531
C3) Arts or arts training? -> 530
    - Other arts -> 530
C4) Events or live performances? -> 468
    - Other events -> 468
C5) "Tamsa" experiences? -> 449
    - Other tamsa -> 449
C6) Otherwise in this theme -> Unknown

Retail & Subscriptions:
RS1) Magazine subscription? -> 442
    - Any magazine subscription -> 442
RS2) Publication/periodical subscription (non-magazine)? -> 378
    - Other publication subscription -> 378
RS3) Gift sets? -> 375
    - Other gift sets -> 375
RS4) Store gift vouchers? -> 376
    - Other store gift vouchers -> 376
RS5) Shopping center gift cards? -> 377
    - Other shopping center gift cards -> 377
RS6) Charity/meaningful gifts? -> 452
    - Other charity gifts -> 452
RS7) Otherwise in this theme -> Unknown
"""
