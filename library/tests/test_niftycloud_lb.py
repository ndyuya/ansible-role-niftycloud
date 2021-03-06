import os
import sys
sys.path.append('.')
sys.path.append('..')

import unittest
import mock
import niftycloud_lb
import xml.etree.ElementTree as etree

class TestNiftycloud(unittest.TestCase):
	def setUp(self):
		self.mockModule = mock.MagicMock(
			params = dict(
				access_key = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
				secret_access_key = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
				endpoint   = 'west-1.cp.cloud.nifty.com',
				instance_id = 'test001',
				instance_port = 80,
				loadbalancer_name = 'lb001',
				loadbalancer_port = 80,
				state = 'running'
			),
			fail_json = mock.MagicMock(side_effect=Exception('failed'))
		)

		self.xmlnamespace = 'https://cp.cloud.nifty.com/api/'
		self.xml = niftycloud_api_response_sample

		self.mockRequestsGetDescribeLoadBalancers  = mock.MagicMock(
			return_value=mock.MagicMock(
				status_code = 200,
				text = self.xml['describeLoadBalancers']
			))

		self.mockDescribeLoadBalancers = mock.MagicMock(
			return_value=dict(
				status = 200,
				xml_body = etree.fromstring(self.xml['describeLoadBalancers']),
				xml_namespace = dict(nc = self.xmlnamespace)
			))

		self.mockRequestsGetRegisterInstancesWithLoadBalancer  = mock.MagicMock(
			return_value=mock.MagicMock(
				status_code = 200,
				text = self.xml['registerInstancesWithLoadBalancer']
			))

		self.mockRequestsGetDeregisterInstancesFromLoadBalancer = mock.MagicMock(
			return_value=mock.MagicMock(
				status_code = 200,
				text = self.xml['deregisterInstancesFromLoadBalancer']
			))

		self.mockRequestsInternalServerError = mock.MagicMock(
			return_value=mock.MagicMock(
				status_code = 500,
				text = self.xml['describeLoadBalancers']
			))

		self.mockRequestsError = mock.MagicMock(return_value=None)

		patcher = mock.patch('time.sleep')
		self.addCleanup(patcher.stop)
		self.mock_time_sleep = patcher.start()
			
	# calculate signature
	def test_calculate_signature(self):
		secret_access_key = self.mockModule.params['secret_access_key']
		method = 'GET'
		endpoint = self.mockModule.params['endpoint']
		path = '/api/'
		params = dict(
			Action = 'DescribeInstances',
			AccessKeyId = self.mockModule.params['access_key'],
			SignatureMethod = 'HmacSHA256',
			SignatureVersion = '2',
                        InstanceId = self.mockModule.params['instance_id']
		)

		signature = niftycloud_lb.calculate_signature(secret_access_key, method, endpoint, path, params)
		self.assertEqual(signature, 'Y7/0nc3dCK9UNkp+w5sh08ybJLQjh69mXOgcxJijDEU=')

	# method get
	def test_request_to_api_get(self):
		method = 'GET'
		action = 'DescribeLoadBalancers'
		params = dict()

		with mock.patch('requests.get', self.mockRequestsGetDescribeLoadBalancers):
			info = niftycloud_lb.request_to_api(self.mockModule, method, action, params)

		self.assertEqual(info['status'], 200)
		self.assertEqual(info['xml_namespace'], dict(nc = self.xmlnamespace))
		self.assertEqual(etree.tostring(info['xml_body']),
				 etree.tostring(etree.fromstring(self.xml['describeLoadBalancers'])))

	# method failed
	def test_request_to_api_unknown(self):
		method = 'UNKNOWN'
		action = 'DescribeLoadBalancers'
		params = dict()

		self.assertRaises(
			Exception,
			niftycloud_lb.request_to_api,
			(self.mockModule, method, action, params)
		)

	# network error
	def test_request_to_api_error(self):
		method = 'GET'
		action = 'DescribeLoadBalancers'
		params = dict()

		with mock.patch('requests.get', self.mockRequestsError):
			self.assertRaises(
				Exception,
				niftycloud_lb.request_to_api,
				(self.mockModule, method, action, params)
			)

	# describe
	def test_describe_load_balancers(self):
		with mock.patch('requests.get', self.mockRequestsGetDescribeLoadBalancers):
			info = niftycloud_lb.describe_load_balancers(self.mockModule, dict())
		self.assertEqual(info['status'], 200)
		self.assertEqual(info['xml_namespace'], dict(nc = self.xmlnamespace))
		self.assertEqual(etree.tostring(info['xml_body']),
				 etree.tostring(etree.fromstring(self.xml['describeLoadBalancers'])))

	# present
	def test_get_state_instance_in_load_balancer_present(self):
		with mock.patch('requests.get', self.mockRequestsGetDescribeLoadBalancers):
			self.assertEqual(
				'present',
				niftycloud_lb.get_state_instance_in_load_balancer(self.mockModule)
			)

	# absent
	def test_get_state_instance_in_load_balancer_present(self):
		with mock.patch('requests.get', self.mockRequestsGetDescribeLoadBalancers):
			self.mockModule.params['instance_id'] = 'test999'
			self.assertEqual(
				'absent',
				niftycloud_lb.get_state_instance_in_load_balancer(self.mockModule)
			)

	# internal server error
	def test_get_state_instance_in_load_balancer_error(self):
		with mock.patch('requests.get', self.mockRequestsInternalServerError):
			self.assertRaises(
				Exception,
				niftycloud_lb.get_state_instance_in_load_balancer,
				(self.mockModule)
			)


	# is present instance (present)
	def test_is_present_in_load_balancer_present(self):
		with mock.patch('requests.get', self.mockRequestsGetDescribeLoadBalancers):
			self.assertEqual(
				True,
				niftycloud_lb.is_present_in_load_balancer(self.mockModule)
			)

	# is present instance (absent)
	def test_is_present_in_load_balancer_absent(self):
		with mock.patch('requests.get', self.mockRequestsGetDescribeLoadBalancers):
			self.mockModule.params['instance_id'] = 'test999'
			self.assertEqual(
				False,
				niftycloud_lb.is_present_in_load_balancer(self.mockModule)
			)

	# internal server error
	def test_is_present_in_load_balancer_error(self):
		with mock.patch('requests.get', self.mockRequestsInternalServerError):
			self.assertRaises(
				Exception,
				niftycloud_lb.is_present_in_load_balancer,
				(self.mockModule)
			)

	# is absent instance (present)
	def test_is_absent_in_load_balancer_present(self):
		with mock.patch('requests.get', self.mockRequestsGetDescribeLoadBalancers):
			self.assertEqual(
				False,
				niftycloud_lb.is_absent_in_load_balancer(self.mockModule)
			)

	# is absent instance (absent)
	def test_is_absent_in_load_balancer_absent(self):
		with mock.patch('requests.get', self.mockRequestsGetDescribeLoadBalancers):
			self.mockModule.params['instance_id'] = 'test999'
			self.assertEqual(
				True,
				niftycloud_lb.is_absent_in_load_balancer(self.mockModule)
			)

	# internal server error
	def test_is_absent_in_load_balancer_error(self):
		with mock.patch('requests.get', self.mockRequestsInternalServerError):
			self.assertRaises(
				Exception,
				niftycloud_lb.is_absent_in_load_balancer,
				(self.mockModule)
			)

	# absent -> present
	def test_regist_instance_absent(self):
		with mock.patch('requests.get', self.mockRequestsGetRegisterInstancesWithLoadBalancer):
			with mock.patch('niftycloud_lb.is_present_in_load_balancer',
					mock.MagicMock(return_value=False)):
				self.assertEqual(
					(True, 'present'),
					niftycloud_lb.regist_instance(self.mockModule)
				)

	# present -> present
	def test_regist_instance_present(self):
		with mock.patch('requests.get', self.mockRequestsGetRegisterInstancesWithLoadBalancer):
			with mock.patch('niftycloud_lb.is_present_in_load_balancer',
					mock.MagicMock(return_value=True)):
				self.assertEqual(
					(False, 'present'),
					niftycloud_lb.regist_instance(self.mockModule)
				)

	# internal server error
	def test_regist_instance_error(self):
		with mock.patch('requests.get', self.mockRequestsInternalServerError):
			with mock.patch('niftycloud_lb.is_present_in_load_balancer',
					mock.MagicMock(return_value=False)):
				self.assertRaises(
					Exception,
					niftycloud_lb.regist_instance,
					(self.mockModule)
				)

	# deregist
	def test_deregist_instance(self):
		with mock.patch('requests.get', self.mockRequestsGetDeregisterInstancesFromLoadBalancer):
			with mock.patch('niftycloud_lb.describe_load_balancers',
					self.mockDescribeLoadBalancers):
				self.assertEqual(
					(True, 'absent(lb001:80->80)'),
					niftycloud_lb.deregist_instance(self.mockModule)
				)

	# deregist failed
	def test_deregist_instance_failed(self):
		with mock.patch('requests.get', self.mockRequestsGetDeregisterInstancesFromLoadBalancer):
			with mock.patch('niftycloud_lb.describe_load_balancers',
					self.mockDescribeLoadBalancers):
				self.mockModule.params['instance_id'] = 'test999'
				self.assertEqual(
					(False, 'absent()'),
					niftycloud_lb.deregist_instance(self.mockModule)
				)

	# deregist internal server error
	def test_deregist_instance_error(self):
		with mock.patch('requests.get', self.mockRequestsInternalServerError):
			with mock.patch('niftycloud_lb.describe_load_balancers',
					self.mockDescribeLoadBalancers):
				self.assertRaises(
					Exception,
					niftycloud_lb.deregist_instance,
					(self.mockModule)
				)

	# deregist internal server error (describe)
	def test_deregist_instance_describe_error(self):
		with mock.patch('niftycloud_lb.describe_load_balancers',
				self.mockRequestsInternalServerError):
			self.assertRaises(
				Exception,
				niftycloud_lb.deregist_instance,
				(self.mockModule)
			)

niftycloud_api_response_sample = dict(
	describeLoadBalancers = '''
<DescribeLoadBalancersResponse xmlns="https://cp.cloud.nifty.com/api/">
<DescribeLoadBalancersResult>
 <LoadBalancerDescriptions>
  <member>
  <LoadBalancerName>lb001</LoadBalancerName>
  <DNSName>111.171.200.1</DNSName>
  <NetworkVolume>10</NetworkVolume>
  <ListenerDescriptions>
   <member>
   <Listener>
    <Protocol>HTTP</Protocol>
    <LoadBalancerPort>80</LoadBalancerPort>
    <InstancePort>80</InstancePort>
    <balancingType>1</balancingType>
    <SSLCertificateId>100</SSLCertificateId>
   </Listener>
   </member>
  </ListenerDescriptions>
  <Policies>
   <AppCookieStickinessPolicies>
    <member>
     <PolicyName/>
     <CookieName/>
    </member>
   </AppCookieStickinessPolicies>
   <LBCookieStickinessPolicies>
    <member>
     <PolicyName/>
     <CookieExpirationPeriod/>
    </member>
   </LBCookieStickinessPolicies>
  </Policies>
  <AvailabilityZones>
   <member>east-11</member>
  </AvailabilityZones>
  <Instances>
   <member>
   <InstanceId>test001</InstanceId>
   <InstanceUniqueId>i-asdg1234</InstanceUniqueId>
   </member>
  </Instances>
  <HealthCheck>
   <Target>TCP:80</Target>
   <Interval>300</Interval>
   <Timeout>900</Timeout>
   <UnhealthyThreshold>3</UnhealthyThreshold>
   <HealthyThreshold>1</HealthyThreshold>
   <InstanceStates>
    <member>
     <InstanceId>Server001</InstanceId>
     <InstanceUniqueId>i-12345678</InstanceUniqueId>
     <State>InService</State>
     <ResponseCode />
     <Description />
    </member>
   </InstanceStates>
  </HealthCheck>
  <Filter>
   <FilterType>1</FilterType>
   <IPAddresses>
    <member>
     <IPAddress>111.111.111.111</IPAddress>
     <IPAddress>111.111.111.112</IPAddress>
    </member>
   </IPAddresses>
  </Filter>
  <CreatedTime>2010-05-17T11:22:33.456Z</CreatedTime>
  <AccountingType>1</AccountingType>
  <NextMonthAccountingType>1</NextMonthAccountingType>
  <Option>    
    <SessionStickinessPolicy> 
      <Enabled>true</Enabled>
      <ExpirationPeriod>10</ExpirationPeriod>
    </SessionStickinessPolicy>
    <SorryPage>
      <Enabled>true</Enabled>
      <StatusCode>200</StatusCode>
    </SorryPage>
  </Option>
  </member>
 </LoadBalancerDescriptions>
 </DescribeLoadBalancersResult>
  <ResponseMetadata>
    <RequestId>f6dd8353-eb6b-6b4fd32e4f05</RequestId>
  </ResponseMetadata>
</DescribeLoadBalancersResponse>
''',
	registerInstancesWithLoadBalancer = '''
<RegisterInstancesWithLoadBalancerResponse xmlns="https://cp.cloud.nifty.com/api/">
  <RegisterInstancesWithLoadBalancerResult>
    <Instances>
      <member>
        <InstanceId>test001</InstanceId>
        <instanceUniqueId>i-asda1234</instanceUniqueId>
      </member>
    </Instances>
  </RegisterInstancesWithLoadBalancerResult>
  <ResponseMetadata>
    <RequestId>f6dd8353-eb6b-6b4fd32e4f05</RequestId>
  </ResponseMetadata>
</RegisterInstancesWithLoadBalancerResponse>
''',
	deregisterInstancesFromLoadBalancer = '''
<DeregisterInstancesFromLoadBalancerResponse xmlns="https://cp.cloud.nifty.com/api/">
  <DeregisterInstancesFromLoadBalancerResult>
    <Instances>
      <member>
        <InstanceId>test001</InstanceId>
        <instanceUniqueId>i-abvf1234</instanceUniqueId>
      </member>
    </Instances>
  </DeregisterInstancesFromLoadBalancerResult>
  <ResponseMetadata>
    <RequestId>f6dd8353-eb6b-6b4fd32e4f05</RequestId>
  </ResponseMetadata>
</DeregisterInstancesFromLoadBalancerResponse>
'''
)

if __name__ == '__main__':
	unittest.main()
