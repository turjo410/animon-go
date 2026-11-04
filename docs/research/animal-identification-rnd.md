# Animal identification R&D next steps

**Research updated:** 4 November 2026  
**Goal:** recognize the same real animal across different players’ scans, without training our own model.  
**Status:** desk research; the services and models below have not been benchmarked by us.

## Recommendation

**Run a small cats-and-dogs pilot using Petnow’s Petify before committing to an identification provider.** It offers guided capture and individual matching without us training a model. The first question is whether people can complete that capture naturally during an encounter—not just whether the matching API works.

Keep reliable individual identification across cats, dogs, birds and insects as the long-term research goal. The evidence reviewed does not establish a ready-made solution that meets that entire requirement from casual phone scans.

## Options worth pursuing

| Option | What it offers | What we should do |
| --- | --- | --- |
| **Petify** | Registration and individual identification for dogs and cats; hosted capture links, mobile SDKs and a server API. | Test first because it requires the least model work. It searches our registered pets, rather than every animal worldwide. [Capture documentation](https://docs.petnow.io/petify/docs/server/web-integration/intro) |
| **Hosted MiewID through Wild Me** | Matches animal photographs against an existing catalog. New individuals can be added without retraining. The current official page describes v4.1 coverage of 93 species. | A possible broader alternative. Confirm supported everyday species, commercial game use, integration access and pricing with the provider before committing. Its models are currently licensed only for Conservation X Labs-hosted applications. [Official model and licensing information](https://www.wildme.org/miewid.html) |
| **Dedicated bird and insect research** | Individual recognition has been demonstrated for selected bird populations and reed bees in specific studies. | Treat these as separate feasibility studies. Those results do not establish dependable matching for arbitrary outdoor encounters. [Bird study](https://doi.org/10.1111/2041-210X.13436), [insect study](https://arxiv.org/abs/2405.13376) |

**Correction to the earlier recommendation:** public access to MiewID weights should not be treated as permission to self-host them. Follow the provider’s current licensing statement.

## What we should do now

1. **Test the capture experience first.** Try Petify’s guided live capture with a few consenting pet owners. Record completion time, retries and failed captures. Its documentation describes live capture and rejects photographs or monitor images; this is a different experience from taking an ordinary animal photo. Stop this route if capture is impractical for our intended encounters. [Capture requirements](https://docs.petnow.io/petify/docs/server/web-integration/intro)
2. **Run a small identity pilot.** Suggested starting sample: 30 known pets, split between cats and dogs. Register 20 and keep 10 unregistered. Rescan across two people, two phones and separate days; include similar-looking animals. Collecting reference examples is still necessary even when no model training is needed.
3. **Measure the right outcomes.** Record correct repeat matches, wrong-animal matches, unknown animals incorrectly matched, uncertain results, capture completion and total response time. Keep failed attempts in the results. A small successful pilot is a reason to expand testing, not proof of production reliability.
4. **Check duplicate collection behavior.** A confident existing match should reuse its animal record. Uncertain scans must wait for more evidence; “no match” alone must not automatically prove a new animal. Test repeat enrollment and simultaneous collection attempts.
5. **Choose the next route from the evidence.** If capture and matching both work, expand the pet pilot and use server-verified results for collection decisions. If capture fails, investigate hosted MiewID’s fit and commercial terms. If every bird and insect must support exclusive collection immediately, the reviewed options do not yet satisfy the requirement; record that gap explicitly.

## Cost and decision

Petify currently lists **Plus at US$0.75 per registered pet per month**, including 1:N identification. That is approximately **US$750 monthly for 1,000 registered pets**, before our own infrastructure costs. Core is US$0.50 but lacks 1:N identification, so it does not meet the cross-player search requirement. Confirm trial entitlements and billing before a paid pilot. [Current pricing](https://www.petnow.io/en/pricing)

**Next deliverable:** a short pilot result sheet showing capture practicality, matching failures, recurring cost and a go/no-go recommendation for a larger trial. Defer custom model training until these tests show why an existing service cannot meet the need.
