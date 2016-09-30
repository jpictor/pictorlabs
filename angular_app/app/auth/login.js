'use strict';

angular.module('myApp.auth.login', ['ngRoute'])

    .config(['$routeProvider', function ($routeProvider) {
        $routeProvider.when('/login', {
            templateUrl: 'auth/login.html',
            controller: 'LoginCtrl'
        });
    }])

    .controller('LoginCtrl', function ($scope, $window, $rootScope, $location, Restangular) {
        $scope.inputUsername = null;
        $scope.inputPassword = null;
        $scope.incorrectPassword = false;

        $scope.submit = function () {
            var postData = {username: $scope.inputUsername, password: $scope.inputPassword};
            Restangular.all('session/login').post(postData).then(function(chkResp) {
                $rootScope.userIsAuthenticated = true;
                var nextUrl = $location.search().next;
                if (nextUrl) {
                    $window.location = nextUrl;
                } else {
                    $location.path('/app/');
                }
            }, function(response) {
                $scope.incorrectPassword = true;
            });
        }
    });
