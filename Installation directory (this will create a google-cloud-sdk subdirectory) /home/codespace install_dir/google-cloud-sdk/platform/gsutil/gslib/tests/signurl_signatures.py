TEST_SIGN_PUT_SIG = (
    'https://storage.googleapis.com/test/test.txt?x-goog-signature='
    '9701aa8c722487256002e5a7532ad991703075e6f71a26af8107147635cc2a'
    '61680dc33548b3e8b43575a5d30b06b36365207bc96bda0ec3dc5605928cce'
    'd393178307de10e96b6f38bd2686178e4a20dff3022e5fb938e6f85e7a433c'
    '7a7ba9d7a64d889a484464e6f9bf4a8582e93c82e5c7b1ad9cfa793be2db72'
    '14bbcd8ab0aba70ec7043eb496202185a265738c000555880b1e3f8a73cd19'
    '8c0e805b73fe4ac21a102f262ea5e10103fa4ecdc69e6bc280212f9f1773cc'
    'd603b854f4c7df8c47325023641e06cb5afac537f3fe68a5786715745005cb'
    'fb38750d7a9f0ae9de7a77466428baa668e507b10bdcf3d0eb596134318292'
    '15bb532c2e174160&x-goog-algorithm=GOOG4-RSA-SHA256&x-goog-cred'
    'ential=test.apps.googleusercontent.com%2F19000101%2Fus-east%2F'
    'storage%2Fgoog4_request&x-goog-date=19000101T000555Z&x-goog-ex'
    'pires=3600&x-goog-signedheaders=host%3Bx-goog-resumable')

TEST_SIGN_RESUMABLE = (
    'https://storage.googleapis.com/test/test.txt?x-goog-signature='
    '9701aa8c722487256002e5a7532ad991703075e6f71a26af8107147635cc2a'
    '61680dc33548b3e8b43575a5d30b06b36365207bc96bda0ec3dc5605928cce'
    'd393178307de10e96b6f38bd2686178e4a20dff3022e5fb938e6f85e7a433c'
    '7a7ba9d7a64d889a484464e6f9bf4a8582e93c82e5c7b1ad9cfa793be2db72'
    '14bbcd8ab0aba70ec7043eb496202185a265738c000555880b1e3f8a73cd19'
    '8c0e805b73fe4ac21a102f262ea5e10103fa4ecdc69e6bc280212f9f1773cc'
    'd603b854f4c7df8c47325023641e06cb5afac537f3fe68a5786715745005cb'
    'fb38750d7a9f0ae9de7a77466428baa668e507b10bdcf3d0eb596134318292'
    '15bb532c2e174160&x-goog-algorithm=GOOG4-RSA-SHA256&x-goog-cred'
    'ential=test.apps.googleusercontent.com%2F19000101%2Fus-east%2F'
    'storage%2Fgoog4_request&x-goog-date=19000101T000555Z&x-goog-ex'
    'pires=3600&x-goog-signedheaders=host%3Bx-goog-resumable')

TEST_SIGN_URL_PUT_CONTENT = (
    'https://storage.googleapis.com/test/test.txt?x-goog-signature='
    '9743fbea283c92e23753e740b9d1541876ed606be21d12c70d3b4bccd63552'
    '71bade73a86c846af0bfe7c53eef18132851569378cb21795be6a46e60a086'
    '4c57e80986cc1952e75e2237bde0d619741fe191646a40a9be593a3a3bf0e6'
    '855efefe6c39ebdbb82e49bfc0cae3492d400d4d50909861398a02032ad771'
    'f446c63ead6c5e35d6bf8c3f47e7d1f6b076c4cf2e5f33e30e2a560830a947'
    'c4ff7ba40c2dfab7e9e1a3f8a7fcf9d7715f94b8b3b19e4c1cd3a954142521'
    '7ec95bbdf484c56779623066f77756af67375f27607c25ec92de51d6ed1fa0'
    '0d4f0b901412ebd963e08ed328812be2bd6742871f7272ca681a7e3170684b'
    '53f8142aeb39b704&x-goog-algorithm=GOOG4-RSA-SHA256&x-goog-cred'
    'ential=test.apps.googleusercontent.com%2F19000101%2Feu%2Fstora'
    'ge%2Fgoog4_request&x-goog-date=19000101T000555Z&x-goog-expires'
    '=3600&x-goog-signedheaders=content-type%3Bhost')

TEST_SIGN_URL_GET = (
    'https://storage.googleapis.com/test/test.txt?x-goog-signature='
    '3ee945ed5fdc7da8a88f391aa0b51e69b3abef015f8271cdc767856f0bc1ae'
    'b6a1e3dd9afc9cfdd769e2e6af1256f7d6a84ad52e02e422fb69e05a88fd6a'
    'cdb92d971ab2db7f9ad368b414ea912d31118abd94932842cce1aa98ecb21d'
    'c2f2507c9f6231db617163a012185b08c3eca1be9aef8adde61c5a44a4d2a3'
    '52e1b5d8180594ea826ea099645f90dd3629ee7a89357bfc36c9097fb6b774'
    '92c692d64aaab63611162b3c43c88ff9f49921fa4ee4638ce7a9eaac455106'
    '948d6ab7bb08ae9fc7312541c92720edcd64620d37e2f49e0ea112cea783db'
    'aaa8b08d81a5208c405d7547e715198325dd7ef1e5db16dd315addd8cf28f6'
    '8b65007b0ef82026&x-goog-algorithm=GOOG4-RSA-SHA256&x-goog-cred'
    'ential=test.apps.googleusercontent.com%2F19000101%2Fasia%2Fsto'
    'rage%2Fgoog4_request&x-goog-date=19000101T000555Z&x-goog-expir'
    'es=0&x-goog-signedheaders=host')

TEST_SIGN_URL_GET_WITH_JSON_KEY = (
    'https://storage.googleapis.com/test/test.txt?x-goog-signature='
    '2ed227f18d31cdf2b01da7cd4fcea45330fbfcc0dda1d327a8c27124a276ee'
    'e0de835e9cd4b0bee609d6b4b21a88a8092a9c089574a300243dde38351f0d'
    '183df007211ded41f2f0854290b995be6c9d0367d9c00976745ba27740238b'
    '0dd49fee7c41e7ed1569bbab8ffbb00a2078e904ebeeec2f8e55e93d4baba1'
    '3db5dc670b1b16183a15d5067f1584db88b3dc55e3edd3c97c0f31fec99ea4'
    'ce96ddb8235b0352c9ce5110dad1a580072d955fe9203b6701364ddd85226b'
    '55bec84ac46e48cd324fd5d8d8ad264d1aa0b7dbad3ac04b87b2a6c2c8ef95'
    '3285cbe3b431e5def84552e112899459fcb64d2d84320c06faa1e8efa26eca'
    'cce2eff41f2d2364&x-goog-algorithm=GOOG4-RSA-SHA256&x-goog-cred'
    'ential=test%40developer.gserviceaccount.com%2F19000101%2Fasia%'
    '2Fstorage%2Fgoog4_request&x-goog-date=19000101T000555Z&x-goog-'
    'expires=0&x-goog-signedheaders=host')

TEST_SIGN_URL_PUT_WITH_SERVICE_ACCOUNT = (
    'https://storage.googleapis.com/test/test.txt?x-goog-signature='
    '66616b655f7369676e6174757265&x-goog-algorithm=GOOG4-RSA-SHA256'
    '&x-goog-credential=fake_service_account_email%2F19000101%2Fus-'
    'east1%2Fstorage%2Fgoog4_request&x-goog-date=19000101T000555Z&x'
    '-goog-expires=3600&x-goog-signedheaders=host')
TEST_SIGN_URL_GET_USERPROJECT = (
    'https://storage.googleapis.com/test/test.txt?x-goog-signature='
    '2a461e23321fbc6d6346848836a0b82fd53b796a58421e9978ac6ca011e2b4'
    '557aa7db63328c9d3f2dacd98b3c3b13d849a25df813b1efefd448ce7a2c27'
    '9851383b772f84b461dfafb4f2af4bec98d224880ea3b1be61ab447614ec1f'
    '735b45aaedca9b257969d7bac69d64f7e2c4ea4b5c18cb2b04afff03fe0b8f'
    'ba9d85bfce6ba81f5354070938bfd6bce614204a63e58098d47b66a711a9ac'
    '44e2dfd06d3183e8007d8fb9c221ac79fee306c8b6a123d5918a586bb0fde9'
    'e945a14ae1264496fe4146fcf92f9f1ed4a13880ec13543ffbcf4c985db2f2'
    '01b287184f1f89dd14d2c801c26275c8f7f348e3eb3456c4ff42dcc0ae7fee'
    '4e8c03b1e8a57570&userProject=myproject&x-goog-algorithm=GOOG4-'
    'RSA-SHA256&x-goog-credential=test.apps.googleusercontent.com%2'
    'F19000101%2Fasia%2Fstorage%2Fgoog4_request&x-goog-date=1900010'
    '1T000555Z&x-goog-expires=0&x-goog-signedheaders=host')
