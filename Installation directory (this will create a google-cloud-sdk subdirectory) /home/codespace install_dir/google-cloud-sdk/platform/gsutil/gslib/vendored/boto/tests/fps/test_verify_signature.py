from boto.fps.connection import FPSConnection

def test():
    conn = FPSConnection()
    # example response from the docs
    params = 'expiry=08%2F2015&signature=ynDukZ9%2FG77uSJVb5YM0cadwHVwYKPMKOO3PNvgADbv6VtymgBxeOWEhED6KGHsGSvSJnMWDN%2FZl639AkRe9Ry%2F7zmn9CmiM%2FZkp1XtshERGTqi2YL10GwQpaH17MQqOX3u1cW4LlyFoLy4celUFBPq1WM2ZJnaNZRJIEY%2FvpeVnCVK8VIPdY3HMxPAkNi5zeF2BbqH%2BL2vAWef6vfHkNcJPlOuOl6jP4E%2B58F24ni%2B9ek%2FQH18O4kw%2FUJ7ZfKwjCCI13%2BcFybpofcKqddq8CuUJj5Ii7Pdw1fje7ktzHeeNhF0r9siWcYmd4JaxTP3NmLJdHFRq2T%2FgsF3vK9m3gw%3D%3D&signatureVersion=2&signatureMethod=RSA-SHA1&certificateUrl=https%3A%2F%2Ffps.sandbox.amazonaws.com%2Fcerts%2F090909%2FPKICert.pem&tokenID=A5BB3HUNAZFJ5CRXIPH72LIODZUNAUZIVP7UB74QNFQDSQ9MN4HPIKISQZWPLJXF&status=SC&callerReference=callerReferenceMultiUse1'
    endpoint = 'http://vamsik.desktop.amazon.com:8080/ipn.jsp'
    conn.verify_signature(endpoint, params)


if __name__ == '__main__':
    test()
