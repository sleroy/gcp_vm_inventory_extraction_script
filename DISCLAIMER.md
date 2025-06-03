# Disclaimer

## No Warranty

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Data Collection and Storage

This tool:
- Does NOT collect or store any data in the cloud
- Processes data only in memory and on your local machine
- Exports data only to your specified local directory
- Does not transmit any collected information to external servers

## Security Recommendations

For maximum security:
1. Review the source code before use
2. Use a dedicated Google service account with minimal permissions as specified in the README
3. Revoke service account keys after use if they are no longer needed
4. Use the `--check-apis-only` option first to verify what APIs will be accessed

## Open Source

This tool is open source and the complete code can be reviewed at:
https://github.com/sleroy/gcp_vm_inventory_extraction_script

## Usage Agreement

By using this tool, you acknowledge that:
1. You have reviewed and accepted this disclaimer
2. You have the necessary permissions to access the GCP resources being inventoried
3. You will use this tool in compliance with your organization's security policies
4. You understand that you are responsible for the security of any exported data
