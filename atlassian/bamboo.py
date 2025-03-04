# coding=utf-8
import logging
from .rest_client import AtlassianRestAPI

log = logging.getLogger(__name__)


class Bamboo(AtlassianRestAPI):
    def _get_generator(self, path, elements_key='results', element_key='result', data=None, flags=None,
                       params=None, headers=None, max_results=None):
        """
        Generic method to return a generator with the results returned from Bamboo. It is intended to work for
        responses in the form:
        {
            'results':
            {
                'size': 5,
                'start-index': 0,
                'max-result': 5,
                'result': []
            },
            ...
        }
        In this case we would have elements_key='results' element_key='result'.
        The only reason to use this generator is to abstract dealing with response pagination from the client

        :param path: URI for the resource
        :return: generator with the contents of response[elements_key][element_key]
        """
        start_index = 0
        params['start-index'] = start_index
        response = self.get(path, data, flags, params, headers)
        results = response[elements_key]
        size = 0 

        # Check if we still can get results
        if size > max_results or results['size'] == 0:
            return
        for r in results[element_key]:
            size += 1
            yield r
        start_index += results['max-result']

    def base_list_call(self, resource, expand, favourite, clover_enabled, max_results, label=None, start_index=0, **kwargs):
        flags = []
        params = {'max-results': max_results}
        if expand:
            params['expand'] = expand
        if favourite:
            flags.append('favourite')
        if clover_enabled:
            flags.append('cloverEnabled')
        if label:
            params['label'] = label
        params.update(kwargs)
        if 'elements_key' in kwargs and 'element_key' in kwargs:
            return self._get_generator(self.resource_url(resource), flags=flags, params=params,
                                       elements_key=kwargs['elements_key'],
                                       element_key=kwargs['element_key'],
                                       max_results=max_results)
        params['start-index'] = start_index
        return self.get(self.resource_url(resource), flags=flags, params=params)
        
    def get_custom_expiry(self, limit=25):
        """
        Get list of all plans where user has admin permission and which override global expiry settings. 
        If global expiry is not enabled it returns empty response.
        :param limit:
        """
        url = "rest/api/latest/admin/expiry/custom/plan?limit={}".format(limit)
        return self.get(url)

    def plan_directory_info(self, plan_key):
        """
        Returns information about the directories where artifacts, build logs, and build results will be stored. 
        Disabled by default. 
        See https://confluence.atlassian.com/display/BAMBOO/Plan+directory+information+REST+API for more information.
        :param plan_key:
        :return:
        """
        resource = 'planDirectoryInfo/{}'.format(plan_key)
        return self.get(self.resource_url(resource))

    def projects(self, expand=None, favourite=False, clover_enabled=False, max_results=25):
        return self.base_list_call('project', expand, favourite, clover_enabled, max_results,
                                   elements_key='projects', element_key='project')

    def project(self, project_key, expand=None, favourite=False, clover_enabled=False):
        resource = 'project/{}'.format(project_key)
        return self.base_list_call(resource, expand, favourite, clover_enabled, start_index=0, max_results=25)

    def project_plans(self, project_key):
        """
        Returns a generator with the plans in a given project
        :param project_key: Project key
        :return: Generator with plans
        """
        resource = 'project/{}'.format(project_key, max_results=25)
        return self.base_list_call(resource, expand='plans', favourite=False, clover_enabled=False, max_results=25,
                                   elements_key='plans', element_key='plan')

    def plans(self, expand=None, favourite=False, clover_enabled=False, start_index=0, max_results=25):
        return self.base_list_call("plan", expand, favourite, clover_enabled, start_index, max_results,
                                   elements_key='plans', element_key='plan')

    def results(self, project_key=None, plan_key=None, job_key=None, build_number=None, expand=None, favourite=False,
                clover_enabled=False, issue_key=None, label=None, start_index=0, max_results=25, include_all_states=False):
        """
        Get results as generic method
        :param project_key:
        :param plan_key:
        :param job_key:
        :param build_number:
        :param expand:
        :param favourite:
        :param clover_enabled:
        :param issue_key:
        :param label:
        :param start_index:
        :param max_results:
        :param include_all_states:
        :return:
        """
        resource = "result"
        if project_key and plan_key and job_key and build_number:
            resource += "/{}-{}-{}/{}".format(project_key, plan_key, job_key, build_number)
        elif project_key and plan_key and build_number:
            resource += "/{}-{}/{}".format(project_key, plan_key, build_number)
        elif project_key and plan_key:
            resource += "/{}-{}".format(project_key, plan_key)
        elif project_key:
            resource += '/' + project_key

        params = {}
        if issue_key:
            params['issueKey'] = issue_key
        if include_all_states:
            params['includeAllStates'] = include_all_states
        return self.base_list_call(resource, expand=expand, favourite=favourite, clover_enabled=clover_enabled,
                                   start_index=start_index, max_results=max_results,
                                   elements_key='results', element_key='result', label=label, **params)

    def latest_results(self, expand=None, favourite=False, clover_enabled=False, label=None, issue_key=None,
                       start_index=0, max_results=25, include_all_states=False):
        """
        Get latest Results
        :param expand:
        :param favourite:
        :param clover_enabled:
        :param label:
        :param issue_key:
        :param start_index:
        :param max_results:
        :param include_all_states:
        :return:
        """
        return self.results(expand=expand, favourite=favourite, clover_enabled=clover_enabled,
                            label=label, issue_key=issue_key, start_index=start_index, max_results=max_results, include_all_states=include_all_states)

    def project_latest_results(self, project_key, expand=None, favourite=False, clover_enabled=False, label=None,
                               issue_key=None, start_index=0, max_results=25, include_all_states=False):
        """
        Get latest Project Results
        :param project_key:
        :param expand:
        :param favourite:
        :param clover_enabled:
        :param label:
        :param issue_key:
        :param start_index:
        :param max_results:
        :param include_all_states:
        :return:
        """
        return self.results(project_key, expand=expand, favourite=favourite, clover_enabled=clover_enabled,
                            label=label, issue_key=issue_key, start_index=start_index, max_results=max_results, include_all_states=include_all_states)

    def plan_results(self, project_key, plan_key, expand=None, favourite=False, clover_enabled=False, label=None,
                     issue_key=None, start_index=0, max_results=25, include_all_states=False):
        """
        Get Plan results
        :param project_key:
        :param plan_key:
        :param expand:
        :param favourite:
        :param clover_enabled:
        :param label:
        :param issue_key:
        :param start_index:
        :param max_results:
        :param include_all_states:
        :return:
        """
        return self.results(project_key, plan_key, expand=expand, favourite=favourite, clover_enabled=clover_enabled,
                            label=label, issue_key=issue_key, start_index=start_index, max_results=max_results, include_all_states=include_all_states)

    def build_result(self, build_key, expand=None, include_all_states=False):
        """
        Returns details of a specific build result
        :param expand: expands build result details on request. Possible values are: artifacts, comments, labels,
        Jira Issues, stages. stages expand is available only for top level plans. It allows to drill down to job results
        using stages.stage.results.result. All expand parameters should contain results.result prefix.
        :param build_key: Should be in the form XX-YY[-ZZ]-99, that is, the last token should be an integer representing
        the build number
        """
        try:
            int(build_key.split('-')[-1])
            resource = "result/{}".format(build_key)
            return self.base_list_call(resource, expand, favourite=False, clover_enabled=False,
                                       start_index=0, max_results=25, include_all_states=include_all_states)
        except ValueError:
            raise ValueError('The key "{}" does not correspond to a build result'.format(build_key))

    def build_latest_result(self, plan_key, expand=None, include_all_states=False):
        """
        Returns details of a latest build result
        :param expand: expands build result details on request. Possible values are: artifacts, comments, labels,
        Jira Issues, stages. stages expand is available only for top level plans. It allows to drill down to job results
        using stages.stage.results.result. All expand parameters should contain results.result prefix.
        :param plan_key: Should be in the form XX-YY[-ZZ]
        :param include_all_states:
        """
        try:
            resource = "result/{}/latest.json".format(plan_key)
            return self.base_list_call(resource, expand, favourite=False, clover_enabled=False,
                                       start_index=0, max_results=25, include_all_states=include_all_states)
        except ValueError:
            raise ValueError('The key "{}" does not correspond to the latest build result'.format(plan_key))

    def delete_build_result(self, build_key):
        """
        Deleting result for specific build
        :param build_key: Take full build key, example: PROJ-PLAN-8
        """
        custom_resource = '/build/admin/deletePlanResults.action'
        build_key = build_key.split('-')
        plan_key = '{}-{}'.format(build_key[0], build_key[1])
        build_number = build_key[2]
        params = {'buildKey': plan_key, 'buildNumber': build_number}
        return self.post(custom_resource, params=params, headers=self.form_token_headers)

    def delete_plan(self, plan_key):
        """
        Marks plan for deletion. Plan will be deleted by a batch job.
        :param plan_key:
        :return:
        """
        resource = 'rest/api/latest/plan/{}'.format(plan_key)
        return self.delete(resource)

    def reports(self, max_results=25):
        params = {'max-results': max_results}
        return self._get_generator(self.resource_url('chart/reports'), elements_key='reports', element_key='report',
                                   params=params)

    def chart(self, report_key, build_keys, group_by_period, date_filter=None, date_from=None, date_to=None,
              width=None, height=None, start_index=9, max_results=25):
        params = {'reportKey': report_key, 'buildKeys': build_keys, 'groupByPeriod': group_by_period,
                  'start-index': start_index, 'max-results': max_results}
        if date_filter:
            params['dateFilter'] = date_filter
            if date_filter == 'RANGE':
                params['dateFrom'] = date_from
                params['dateTo'] = date_to
        if width:
            params['width'] = width
        if height:
            params['height'] = height
        return self.get(self.resource_url('chart'), params=params)

    def comments(self, project_key, plan_key, build_number, start_index=0, max_results=25):
        resource = "result/{}-{}-{}/comment".format(project_key, plan_key, build_number)
        params = {'start-index': start_index, 'max-results': max_results}
        return self.get(self.resource_url(resource), params=params)

    def create_comment(self, project_key, plan_key, build_number, comment, author=None):
        resource = "result/{}-{}-{}/comment".format(project_key, plan_key, build_number)
        comment_data = {'author': author if author else self.username, 'content': comment}
        return self.post(self.resource_url(resource), data=comment_data)

    def labels(self, project_key, plan_key, build_number, start_index=0, max_results=25):
        resource = "result/{}-{}-{}/label".format(project_key, plan_key, build_number)
        params = {'start-index': start_index, 'max-results': max_results}
        return self.get(self.resource_url(resource), params=params)

    def create_label(self, project_key, plan_key, build_number, label):
        resource = "result/{}-{}-{}/label".format(project_key, plan_key, build_number)
        return self.post(self.resource_url(resource), data={'name': label})

    def delete_label(self, project_key, plan_key, build_number, label):
        resource = "result/{}-{}-{}/label/{}".format(project_key, plan_key, build_number, label)
        return self.delete(self.resource_url(resource))

    def server_info(self):
        return self.get(self.resource_url('info'))

    def agent_status(self):
        return self.get(self.resource_url('agent'))

    def activity(self):
        return self.get('build/admin/ajax/getDashboardSummary.action')

    def deployment_project(self, project_id):
        resource = 'deploy/project/{}'.format(project_id)
        return self.get(self.resource_url(resource))

    def deployment_projects(self):
        resource = 'deploy/project/all'
        for project in self.get(self.resource_url(resource)):
            yield project

    def deployment_environment_results(self, env_id, expand=None, max_results=25):
        resource = 'deploy/environment/{environmentId}/results'.format(environmentId=env_id)
        params = {'max-result': max_results, 'start-index': 0}
        size = 1
        if expand:
            params['expand'] = expand
        while params['start-index'] < size:
            results = self.get(self.resource_url(resource), params=params)
            size = results['size']
            for r in results['results']:
                yield r
            params['start-index'] += results['max-result']

    def deployment_dashboard(self, project_id=None):
        """
        Returns the current status of each deployment environment
        If no project id is provided, returns all projects.
        """
        resource = 'deploy/dashboard/{}'.format(project_id) if project_id else 'deploy/dashboard'
        return self.get(self.resource_url(resource))

    def search_branches(self, plan_key, include_default_branch=True, max_results=25):
        params = {
            'max-result': max_results,
            'start-index': 0,
            'masterPlanKey': plan_key,
            'includeMasterBranch': include_default_branch
        }
        size = 1
        while params['start-index'] < size:
            results = self.get(self.resource_url('search/branches'), params=params)
            size = results['size']
            for r in results['searchResults']:
                yield r
            params['start-index'] += results['max-result']

    def plan_branches(self, plan_key, expand=None, favourite=False, clover_enabled=False, max_results=25):
        """api/1.0/plan/{projectKey}-{buildKey}/branch"""
        resource = 'plan/{}/branch'.format(plan_key)
        return self.base_list_call(resource, expand, favourite, clover_enabled, max_results,
                                   elements_key='branches', element_key='branch')

    def create_branch(self, plan_key, branch_name, vcs_branch=None, enabled=False, cleanup_enabled=False):
        """
        Method for creating branch for a specified plan. 
        You can use vcsBranch query param to define which vcsBranch should newly created branch use. 
        If not specified it will not override vcsBranch from the main plan. 

        :param plan_key: str TST-BLD
        :param branch_name: str new-shiny-branch
        :param vcs_branch: str feature/new-shiny-branch, /refs/heads/new-shiny-branch
        :param enabled: bool
        :param cleanup_enabled: bool
        :return: PUT request
        """
        resource = 'plan/{plan_key}/branch/{branch_name}'.format(plan_key=plan_key, branch_name=branch_name)
        params = {}
        if vcs_branch:
            params = dict(vcsBranch=vcs_branch,
                          enabled='true' if enabled else 'false',
                          cleanupEnabled='true' if cleanup_enabled else 'false')
        return self.put(self.resource_url(resource), params=params)

    def get_branch_info(self, plan_key, branch_name):
        """
        Get information about a plan branch
        :param plan_key: 
        :param branch_name: 
        :return:
        """
        resource = 'plan/{plan_key}/branch/{branch_name}'.format(plan_key=plan_key, branch_name=branch_name)
        return self.get(self.resource_url(resource))
    
    def enable_plan(self, plan_key):
        """
        Enable plan.
        :param plan_key: str TST-BLD
        :return: POST request
        """
        resource = 'plan/{plan_key}/enable'.format(plan_key=plan_key)
        return self.post(self.resource_url(resource))

    def execute_build(self, plan_key, stage=None, execute_all_stages=True, custom_revision=None, **bamboo_variables):
        """
        Fire build execution for specified plan. 
        !IMPORTANT! NOTE: for some reason, this method always execute all stages
        :param plan_key: str TST-BLD
        :param stage: str stage-name
        :param execute_all_stages: bool
        :param custom_revision: str revisionName
        :param bamboo_variables: dict {variable=value} 
        :return: POST request
        """
        headers = self.form_token_headers
        resource = 'queue/{plan_key}'.format(plan_key=plan_key)
        params = {}
        if stage:
            execute_all_stages = False
            params['stage'] = stage
        if custom_revision:
            params['customRevision'] = custom_revision
        params['executeAllStages'] = 'true' if execute_all_stages else 'false'
        if bamboo_variables:
            for key, value in bamboo_variables.items():
                params['bamboo.variable.{}'.format(key)] = value

        return self.post(self.resource_url(resource), params=params, headers=headers)

    def health_check(self):
        """
        Get health status
        https://confluence.atlassian.com/jirakb/how-to-retrieve-health-check-results-using-rest-api-867195158.html
        :return:
        """
        # check as Troubleshooting & Support Tools Plugin
        response = self.get('rest/troubleshooting/1.0/check/')
        if not response:
            # check as support tools
            response = self.get('rest/supportHealthCheck/1.0/check/')
        return response

    def get_users_in_global_permissions(self, start=0, limit=25):
        """
        Provide users in global permissions configuration
        :param start:
        :param limit:
        :return:
        """
        params = {'limit': limit, 'start': start}
        url = 'rest/api/latest/permissions/global/users'
        return self.get(url, params=params)

    def get_groups(self, start=0, limit=25):
        """
        Retrieve a paginated list of groups.
        The authenticated user must have restricted administrative permission or higher to use this resource.
        :param start:
        :param limit:
        :return:
        """
        params = {'limit': limit, 'start': start}
        url = 'rest/api/latest/admin/groups'
        return self.get(url, params=params)

    def create_group(self, group_name):
        """
        Create a new group.
        The authenticated user must have restricted administrative permission or higher to use this resource.
        :param group_name:
        :return:
        """
        url = 'rest/api/latest/admin/groups'
        data = {'name': group_name}
        return self.post(url, data=data)

    def delete_group(self, group_name):
        """
        Deletes the specified group, removing it from the system.
        The authenticated user must have restricted administrative permission or higher to use this resource.
        :param group_name:
        :return:
        """
        url = 'rest/api/latest/admin/groups/{}'.format(group_name)
        return self.delete(url)

    def add_users_into_group(self, group_name, users):
        """
        Add multiple users to a group.
        The list of usernames should be passed as request body.
        The authenticated user must have restricted administrative permission or higher to use this resource.
        :param group_name:
        :param users: list
        :return:
        """
        url = 'rest/api/latest/admin/groups/{}/add-users'.format(group_name)
        return self.post(url, data=users)

    def remove_users_into_group(self, group_name, users):
        """
        Remove multiple users from a group.
        The list of usernames should be passed as request body.
        The authenticated user must have restricted administrative permission or higher to use this resource.
        :param group_name:
        :param users: list
        :return:
        """
        url = 'rest/api/latest/admin/groups/{}/remove-users'.format(group_name)
        return self.delete(url, data=users)

    def get_users_from_group(self, group_name, filter_users=None, start=0, limit=25):
        """
        Retrieves a list of users that are members of a specified group.
        The authenticated user must have restricted administrative permission or higher to use this resource.
        :param filter_users:
        :param group_name:
        :param start:
        :param limit:
        :return:
        """
        params = {'limit': limit, 'start': start}
        if filter_users:
            params = {'filter': filter_users}
        url = 'rest/api/latest/admin/groups/{}/more-members'.format(group_name)
        return self.get(url, params=params)

    def get_users_not_in_group(self, group_name, filter_users='', start=0, limit=25):
        """
        Retrieves a list of users that are not members of a specified group.
        The authenticated user must have restricted administrative permission or higher to use this resource.
        :param filter_users:
        :param group_name:
        :param start:
        :param limit:
        :return:
        """
        params = {'limit': limit, 'start': start}
        if filter_users:
            params = {'filter': filter_users}

        url = 'rest/api/latest/admin/groups/{}/more-non-members'.format(group_name)
        return self.get(url, params=params)

    def get_build_queue(self, expand='queuedBuilds'):
        """
        Lists all the builds waiting in the build queue, adds or removes a build from the build queue.
        May be used also to resume build on manual stage or rerun failed jobs.
        :return:
        """
        params = {'expand': expand}
        return self.get('rest/api/latest/queue', params=params)

    def upload_plugin(self, plugin_path):
        """
        Provide plugin path for upload into Jira e.g. useful for auto deploy
        :param plugin_path:
        :return:
        """
        files = {
            'plugin': open(plugin_path, 'rb')
        }
        headers = {
            'X-Atlassian-Token': 'nocheck'
        }
        upm_token = self.request(method='GET', path='rest/plugins/1.0/', headers=headers, trailing=True).headers[
            'upm-token']
        url = 'rest/plugins/1.0/?token={upm_token}'.format(upm_token=upm_token)
        return self.post(url, files=files, headers=headers)
