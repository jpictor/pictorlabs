'use strict';

// Declare app level module which depends on views, and components

angular.module('myApp', [
    'ngRoute',
    'restangular',
    'chart.js',
    'angularMoment',
    'truncate',
    'ui.grid',
    'ui.grid.pagination',
    'ui.grid.selection',
    'wu.masonry',
    'infinite-scroll',
    'myApp.main',
    'myApp.auth.login',
    'myApp.add_video',
    'myApp.about'
])

    .factory('AuthInterceptor', function($q, $rootScope) {  
        var authInterceptor = {
            responseError: function(response) {
                if (response.status == 401 || response.status == 403) {
                    $rootScope.$broadcast('auth-required', response);
                }
                if (response.status == 502) {
                    $rootScope.serverDown = true;
                }
                return $q.reject(response);
            }
        };
        return authInterceptor;
    })

    .config(function ($routeProvider, $locationProvider, RestangularProvider, $httpProvider) {
        // register interceptor for auth
        $httpProvider.interceptors.push('AuthInterceptor');

        // CSRF configuration to work with Django REST Framework
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.defaults.withCredentials = true;

        // Configure REST-Angular
        RestangularProvider.setRequestSuffix('/');
        RestangularProvider.setBaseUrl('/api');
        RestangularProvider.setDefaultHttpFields({
            withCredentials: true
        });

        // Set an interceptor in order to parse the API response
        // when getting a list of resources
        // configuration for Django REST Framework
        RestangularProvider.setResponseInterceptor(function (data, operation, what) {
            if (operation == 'getList') {
                var resp = data.results;
                resp.forEach(function(i) {
                    if (i.post) {
                        i._post = i.post;
                    }
                });
                resp._count = data.count;
                resp._next = data.next;
                resp._previous = data.previous;
                return resp
            }
            return data;
        });

        $routeProvider.otherwise({redirectTo: '/fs'});
        $locationProvider.html5Mode(true);
    })

    .run(function($rootScope, $location, $window, Restangular) {
        $rootScope.appInitComplete = false;
        $rootScope.serverDown = false;
        $rootScope.userIsAuthenticated = false;
        $rootScope.showAuthenticatedUserApp = function () {
            return $rootScope.appInitComplete && (!$rootScope.serverDown) && rootScope.userIsAuthenticated;
        }
        $rootScope.showLogin = function () {
            return $rootScope.appInitComplete && $rootScope.userIsAuthenticated;
        }
        $rootScope.logout = function() {
            Restangular.all('session/logout').post().then(function(chkResp) {
                $rootScope.userIsAuthenticated = false;
                $rootScope.$broadcast('auth-required');
            }, function(response) {
                // user not logged out!!!
            });
        }

        $rootScope.$on('auth-required', function () {
            $rootScope.userIsAuthenticated = false;
            //if ($location.path() != '/login') {
            //    $location.path('/login');
            //}
        });

        Restangular.one('session/check').get().then(function(chkResp) {
            $rootScope.userIsAuthenticated = true;
            $rootScope.appInitComplete = true;
            if ($location.path() == '/login') {
                $location.path('/app/');
            }
        }, function(response) {
            $rootScope.appInitComplete = true;
        });
    })

    .filter('to_trusted', function($sce) {
        return function(text) {
            return $sce.trustAsHtml(text);
        };
    })

    .directive('errSrc', function() {
         return {
             link: function(scope, element, attrs) {
                 element.bind('error', function() {
                     if (attrs.src != attrs.errSrc) {
                         attrs.$set('src', attrs.errSrc);
                     }
                 });
             }
         }
    });


;
