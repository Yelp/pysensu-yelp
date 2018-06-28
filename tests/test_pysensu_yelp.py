import pysensu_yelp
import mock
import json
import pytest
import six


class TestPySensuYelp:
    test_name = 'then_i_saw_her_face'
    test_runbook = 'now_im_a_believer'
    test_status = 0
    test_output = 'without_a_trace'
    test_team = 'no_doubt_in_my_mind'
    test_page = False
    test_tip = 'but_who_docks_the_docker'
    test_notification_email = 'sensu_test@pley.moc'
    test_check_every = '1M'
    test_realert_every = 99
    test_alert_after = '1Y'
    test_dependencies = ['a_5_year_old']
    test_irc_channels = ['#sensu_test']
    test_slack_channels = ['#sensu_test_slack']
    test_ticket = True
    test_project = 'TEST_SENSU'
    test_source = 'source.test'
    test_tags = ['tag1', 'tag2']
    test_ttl = '30M'

    event_dict = {
        'name': test_name,
        'status': test_status,
        'output': test_output,
        'handler': 'default',
        'team': test_team,
        'runbook': test_runbook,
        'tip': test_tip,
        'notification_email': test_notification_email,
        'interval': pysensu_yelp.human_to_seconds(test_check_every),
        'page': test_page,
        'realert_every': test_realert_every,
        'dependencies': test_dependencies,
        'alert_after': pysensu_yelp.human_to_seconds(test_alert_after),
        'ticket': test_ticket,
        'project': test_project,
        'source': test_source,
        'tags': test_tags,
        'ttl': pysensu_yelp.human_to_seconds(test_ttl),
    }
    event_dict['irc_channels'] = test_irc_channels
    event_dict['slack_channels'] = test_slack_channels
    event_hash = six.b(json.dumps(event_dict))

    def test_human_to_seconds(self):
        assert pysensu_yelp.human_to_seconds('1s') == 1
        assert pysensu_yelp.human_to_seconds('1m1s') == 61
        assert pysensu_yelp.human_to_seconds('1M1m') == 2592060
        assert pysensu_yelp.human_to_seconds('1Y1M1W1D1h1m1s') == 34822861
        assert pysensu_yelp.human_to_seconds('0s') == 0
        assert pysensu_yelp.human_to_seconds(None) is None

        pytest.raises(Exception, pysensu_yelp.human_to_seconds, ('ss'))
        pytest.raises(Exception, pysensu_yelp.human_to_seconds, ('0q'))

    def test_send_event_valid_args(self):
        magic_skt = mock.MagicMock()
        with mock.patch('socket.socket', return_value=magic_skt) as skt_patch:
            pysensu_yelp.send_event(self.test_name, self.test_runbook,
                                    self.test_status, self.test_output,
                                    self.test_team, page=self.test_page, tip=self.test_tip,
                                    notification_email=self.test_notification_email,
                                    check_every=self.test_check_every,
                                    realert_every=self.test_realert_every,
                                    alert_after=self.test_alert_after,
                                    dependencies=self.test_dependencies,
                                    irc_channels=self.test_irc_channels,
                                    slack_channels=self.test_slack_channels,
                                    ticket=self.test_ticket,
                                    project=self.test_project,
                                    source=self.test_source,
                                    tags=self.test_tags,
                                    ttl=self.test_ttl)
            assert skt_patch.call_count == 1
            magic_skt.connect.assert_called_once_with(('169.254.255.254', 3030))
            magic_skt.sendall.assert_called_once_with(self.event_hash + b'\n')
            magic_skt.close.assert_called_once()

    def test_send_event_custom_sensu_host(self):
        magic_skt = mock.MagicMock()
        with mock.patch('socket.socket', return_value=magic_skt) as skt_patch:
            pysensu_yelp.send_event(self.test_name, self.test_runbook,
                                    self.test_status, self.test_output,
                                    self.test_team, page=self.test_page, tip=self.test_tip,
                                    notification_email=self.test_notification_email,
                                    check_every=self.test_check_every,
                                    realert_every=self.test_realert_every,
                                    alert_after=self.test_alert_after,
                                    dependencies=self.test_dependencies,
                                    irc_channels=self.test_irc_channels,
                                    slack_channels=self.test_slack_channels,
                                    ticket=self.test_ticket,
                                    project=self.test_project,
                                    source=self.test_source,
                                    tags=self.test_tags,
                                    ttl=self.test_ttl,
                                    sensu_host='testhost',
                                    sensu_port=666)
            assert skt_patch.call_count == 1
            magic_skt.connect.assert_called_once_with(('testhost', 666))
            magic_skt.sendall.assert_called_once_with(self.event_hash + b'\n')
            magic_skt.close.assert_called_once()

    def test_send_event_no_team(self):
        magic_skt = mock.MagicMock()
        with mock.patch('socket.socket', return_value=magic_skt) as skt_patch:
            with pytest.raises(ValueError):
                pysensu_yelp.send_event(self.test_name, self.test_runbook,
                                        self.test_status, self.test_output,
                                        '', page=self.test_page, tip=self.test_tip,
                                        notification_email=self.test_notification_email,
                                        check_every=self.test_check_every,
                                        realert_every=self.test_realert_every,
                                        alert_after=self.test_alert_after,
                                        dependencies=self.test_dependencies,
                                        irc_channels=self.test_irc_channels,
                                        slack_channels=self.test_slack_channels,
                                        ticket=self.test_ticket,
                                        project=self.test_project,
                                        source=self.test_source,
                                        tags=self.test_tags,
                                        ttl=self.test_ttl)
            skt_patch.assert_not_called()

    def test_no_special_characters_in_name(self):
        magic_skt = mock.MagicMock()
        with mock.patch('socket.socket', return_value=magic_skt):
            for special_char in '!@#$%^&*() ;",<>=+[]':
                test_name = self.test_name + special_char
                with pytest.raises(ValueError):
                    pysensu_yelp.send_event(test_name, self.test_runbook,
                                            self.test_status, self.test_output,
                                            self.test_team, page=self.test_page, tip=self.test_tip,
                                            notification_email=self.test_notification_email,
                                            check_every=self.test_check_every,
                                            realert_every=self.test_realert_every,
                                            alert_after=self.test_alert_after,
                                            dependencies=self.test_dependencies,
                                            irc_channels=self.test_irc_channels,
                                            slack_channels=self.test_slack_channels,
                                            ticket=self.test_ticket,
                                            project=self.test_project,
                                            source=self.test_source,
                                            tags=self.test_tags,
                                            ttl=self.test_ttl)
