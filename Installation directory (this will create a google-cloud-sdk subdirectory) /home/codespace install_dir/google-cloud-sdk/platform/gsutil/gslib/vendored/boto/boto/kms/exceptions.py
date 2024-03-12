# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
from boto.exception import BotoServerError


class InvalidGrantTokenException(BotoServerError):
    pass


class DisabledException(BotoServerError):
    pass


class LimitExceededException(BotoServerError):
    pass


class DependencyTimeoutException(BotoServerError):
    pass


class InvalidMarkerException(BotoServerError):
    pass


class AlreadyExistsException(BotoServerError):
    pass


class InvalidCiphertextException(BotoServerError):
    pass


class KeyUnavailableException(BotoServerError):
    pass


class InvalidAliasNameException(BotoServerError):
    pass


class UnsupportedOperationException(BotoServerError):
    pass


class InvalidArnException(BotoServerError):
    pass


class KMSInternalException(BotoServerError):
    pass


class InvalidKeyUsageException(BotoServerError):
    pass


class MalformedPolicyDocumentException(BotoServerError):
    pass


class NotFoundException(BotoServerError):
    pass
