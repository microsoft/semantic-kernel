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


class LimitExceededException(BotoServerError):
    pass


class ResourceConflictException(BotoServerError):
    pass


class DeveloperUserAlreadyRegisteredException(BotoServerError):
    pass


class TooManyRequestsException(BotoServerError):
    pass


class InvalidParameterException(BotoServerError):
    pass


class ResourceNotFoundException(BotoServerError):
    pass


class InternalErrorException(BotoServerError):
    pass


class NotAuthorizedException(BotoServerError):
    pass
